from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill
from app.schemas.credit_card_bill import (
    CreditCardBillCreate, CreditCardBillUpdate, CreditCardBillRead,
)
from app.schemas.common import SuccessResponse
from app.services.credit_card_bill import recalculate_bill_installment_snapshot

router = APIRouter(prefix="/api/v1/credit-card-bills", tags=["credit-card-bills"])


def _to_read(bill) -> CreditCardBillRead:
    inst_amount = bill.installment_amount or 0
    total = inst_amount + bill.general_spending + bill.carried_forward
    return CreditCardBillRead(
        id=bill.id,
        credit_card_id=bill.credit_card_id,
        billing_year=bill.billing_year,
        billing_month=bill.billing_month,
        due_date=bill.due_date,
        installment_amount=inst_amount / 100,
        general_spending=bill.general_spending / 100,
        total_amount=total / 100,
        is_paid=bill.is_paid,
        paid_amount=bill.paid_amount / 100 if bill.paid_amount is not None else None,
        carried_forward=bill.carried_forward / 100,
        created_at=bill.created_at,
        updated_at=bill.updated_at,
    )


@router.get("", response_model=SuccessResponse[list[CreditCardBillRead]])
def list_credit_card_bills(
    credit_card_id: int | None = Query(None),
    billing_year: int | None = Query(None),
    billing_month: int | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(CreditCardBill)
    if credit_card_id is not None:
        query = query.filter(CreditCardBill.credit_card_id == credit_card_id)
    if billing_year is not None:
        query = query.filter(CreditCardBill.billing_year == billing_year)
    if billing_month is not None:
        query = query.filter(CreditCardBill.billing_month == billing_month)
    bills = query.all()
    return SuccessResponse.of([_to_read(b) for b in bills])


@router.post("", response_model=SuccessResponse[CreditCardBillRead])
def create_credit_card_bill(payload: CreditCardBillCreate, db: Session = Depends(get_db)):
    card = db.query(CreditCard).filter(CreditCard.id == payload.credit_card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "信用卡不存在"})

    bill = CreditCardBill(
        credit_card_id=payload.credit_card_id,
        billing_year=payload.billing_year,
        billing_month=payload.billing_month,
        due_date=payload.due_date,
        general_spending=round(payload.general_spending * 100),
        is_paid=payload.is_paid,
    )
    db.add(bill)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail={"code": "DUPLICATE_BILL", "message": "同卡同月帳單已存在"})
    recalculate_bill_installment_snapshot(db, bill.id)
    db.commit()
    db.refresh(bill)
    return SuccessResponse.of(_to_read(bill))


@router.put("/{bill_id}", response_model=SuccessResponse[CreditCardBillRead])
def update_credit_card_bill(bill_id: int, payload: CreditCardBillUpdate, db: Session = Depends(get_db)):
    bill = db.query(CreditCardBill).filter(CreditCardBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "帳單不存在"})
    update_data = payload.model_dump(exclude_unset=True)
    if "general_spending" in update_data and update_data["general_spending"] is not None:
        update_data["general_spending"] = round(update_data["general_spending"] * 100)
    if "paid_amount" in update_data and update_data["paid_amount"] is not None:
        update_data["paid_amount"] = round(update_data["paid_amount"] * 100)
    for key, value in update_data.items():
        setattr(bill, key, value)
    # 部分繳款時觸發結轉（本金 + 利息流入下期帳單）
    if "paid_amount" in update_data and update_data.get("paid_amount") is not None:
        from app.services.revolving_interest import calculate_and_carry_forward
        calculate_and_carry_forward(db, bill_id=bill.id, paid_amount_cents=bill.paid_amount)
    db.commit()
    db.refresh(bill)
    return SuccessResponse.of(_to_read(bill))


@router.delete("/{bill_id}", response_model=SuccessResponse[dict])
def delete_credit_card_bill(bill_id: int, db: Session = Depends(get_db)):
    bill = db.query(CreditCardBill).filter(CreditCardBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "帳單不存在"})
    db.delete(bill)
    db.commit()
    return SuccessResponse.of({"deleted": bill_id})
