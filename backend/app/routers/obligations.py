from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.obligation import Obligation
from app.models.installment import Installment
from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill
from app.schemas.obligation import (
    ObligationCreate, ObligationUpdate, ObligationRead, ObligationType, to_read,
)
from app.schemas.common import SuccessResponse
from app.services.credit_card_bill import calc_first_period_date, recalculate_card_unpaid_snapshots

router = APIRouter(prefix="/api/v1/obligations", tags=["obligations"])


@router.get("", response_model=SuccessResponse[list[ObligationRead]])
def list_obligations(
    type: ObligationType | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Obligation)
    if type:
        query = query.filter(Obligation.type == type.value)
    obligations = query.all()

    result = []
    for o in obligations:
        inst = None
        if o.type == "installment":
            inst = db.query(Installment).filter(Installment.obligation_id == o.id).first()
        result.append(to_read(o, inst))
    return SuccessResponse.of(result)


@router.post("", response_model=SuccessResponse[ObligationRead])
def create_obligation(payload: ObligationCreate, db: Session = Depends(get_db)):
    obligation = Obligation(
        name=payload.name,
        type=payload.type.value,
        amount=round(payload.amount * 100),
        frequency=payload.frequency.value,
        start_date=payload.start_date,
        end_date=payload.end_date,
        next_due_date=payload.next_due_date,
        note=payload.note,
    )
    db.add(obligation)
    db.flush()  # get obligation.id

    installment = None
    if payload.type == ObligationType.installment and payload.installment:
        inst = payload.installment
        # Validate credit_card_id exists
        card = db.query(CreditCard).filter(CreditCard.id == inst.credit_card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "信用卡不存在"})

        total_cents = round(inst.total_amount * 100)
        monthly_cents = round(payload.amount * 100)  # obligation.amount = monthly_amount

        if inst.installment_type == "bill":
            # Bill installment: validate source bill
            source_bill = db.query(CreditCardBill).filter(
                CreditCardBill.id == inst.source_bill_id
            ).first()
            if not source_bill:
                raise HTTPException(
                    status_code=404,
                    detail={"code": "NOT_FOUND", "message": "來源帳單不存在"},
                )
            # 已繳帳單不可轉分期
            if source_bill.is_paid:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "VALIDATION_ERROR", "message": "此帳單已繳清或已轉分期，不可重複操作"},
                )
            # credit_card_id 一致性
            if source_bill.credit_card_id != inst.credit_card_id:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "VALIDATION_ERROR", "message": "來源帳單與指定信用卡不一致"},
                )

            # Mark source bill as paid
            source_bill.is_paid = True

            # effective_from_period = next billing cycle after source bill
            if source_bill.billing_month == 12:
                effective_from = date(source_bill.billing_year + 1, 1, card.billing_day)
            else:
                effective_from = date(source_bill.billing_year, source_bill.billing_month + 1, card.billing_day)

            first_period = effective_from

            # 覆寫 obligation 的 start_date 和 next_due_date 使其與 effective_from 一致
            obligation.start_date = effective_from
            obligation.next_due_date = effective_from
        else:
            # Purchase installment: use existing logic
            first_period = calc_first_period_date(payload.start_date, card.billing_day)
            effective_from = None

        installment = Installment(
            obligation_id=obligation.id,
            credit_card_id=inst.credit_card_id,
            installment_type=inst.installment_type,
            total_amount=total_cents,
            monthly_amount=monthly_cents,
            total_periods=inst.total_periods,
            remaining_periods=inst.total_periods,
            interest_rate=inst.interest_rate,
            fee=round(inst.fee * 100) if inst.fee is not None else None,
            current_period_date=first_period,
            source_bill_id=inst.source_bill_id,
            effective_from_period=effective_from,
        )
        db.add(installment)
        db.flush()
        recalculate_card_unpaid_snapshots(db, inst.credit_card_id)

    db.commit()
    db.refresh(obligation)
    if installment:
        db.refresh(installment)
    return SuccessResponse.of(to_read(obligation, installment))


@router.put("/{obligation_id}", response_model=SuccessResponse[ObligationRead])
def update_obligation(obligation_id: int, payload: ObligationUpdate, db: Session = Depends(get_db)):
    obligation = db.query(Obligation).filter(Obligation.id == obligation_id).first()
    if not obligation:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "義務不存在"})
    update_data = payload.model_dump(exclude_unset=True)
    if "amount" in update_data and update_data["amount"] is not None:
        update_data["amount"] = round(update_data["amount"] * 100)
    if "type" in update_data and update_data["type"] is not None:
        update_data["type"] = update_data["type"].value
    if "frequency" in update_data and update_data["frequency"] is not None:
        update_data["frequency"] = update_data["frequency"].value
    for key, value in update_data.items():
        setattr(obligation, key, value)

    # 分期金額變更時，同步 monthly_amount 並觸發 snapshot recalculate
    if obligation.type == "installment" and "amount" in update_data:
        installment = db.query(Installment).filter(Installment.obligation_id == obligation.id).first()
        if installment:
            installment.monthly_amount = obligation.amount
            db.flush()
            recalculate_card_unpaid_snapshots(db, installment.credit_card_id)

    db.commit()
    db.refresh(obligation)
    return SuccessResponse.of(to_read(obligation))


@router.delete("/{obligation_id}", response_model=SuccessResponse[dict])
def delete_obligation(obligation_id: int, db: Session = Depends(get_db)):
    obligation = db.query(Obligation).filter(Obligation.id == obligation_id).first()
    if not obligation:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "義務不存在"})

    # 刪除前記錄 credit_card_id（cascade 刪除後 installment 不可查）
    credit_card_id = None
    if obligation.type == "installment":
        installment = db.query(Installment).filter(Installment.obligation_id == obligation.id).first()
        if installment:
            credit_card_id = installment.credit_card_id

    db.delete(obligation)
    db.flush()

    if credit_card_id is not None:
        recalculate_card_unpaid_snapshots(db, credit_card_id)

    db.commit()
    return SuccessResponse.of({"deleted": obligation_id})
