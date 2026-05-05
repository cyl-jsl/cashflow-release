from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.income import Income
from app.models.income_adjustment import IncomeAdjustment
from app.schemas.common import SuccessResponse
from app.schemas.income_adjustment import IncomeAdjustmentCreate, IncomeAdjustmentRead
from app.utils.date_helpers import advance_date

router = APIRouter(prefix="/api/v1", tags=["income-adjustments"])

_RECURRING = {"monthly", "biweekly", "quarterly", "yearly"}
_MAX_SCHEDULE_LOOKAHEAD = 600


def _is_aligned(income: Income, effective_date: date) -> bool:
    """驗證 effective_date 是否落在 income 的排班日（從 start_date 推進可達）。"""
    current = income.start_date
    for _ in range(_MAX_SCHEDULE_LOOKAHEAD):
        if current == effective_date:
            return True
        if current > effective_date:
            return False
        next_val = advance_date(current, income.frequency)
        if next_val is None:
            return False
        current = next_val
    return False


@router.post(
    "/incomes/{income_id}/actuals",
    response_model=SuccessResponse[IncomeAdjustmentRead],
)
def upsert_income_actual(
    income_id: int,
    body: IncomeAdjustmentCreate,
    db: Session = Depends(get_db),
):
    income = db.get(Income, income_id)
    if not income:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "收入不存在"},
        )
    if income.frequency not in _RECURRING:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FREQUENCY",
                "message": "一次性收入不支援 adjustment",
            },
        )
    if not _is_aligned(income, body.effective_date):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MISALIGNED_DATE",
                "message": f"effective_date 必須對齊 {income.frequency} 排班日",
            },
        )

    actual_cents = round(body.actual_amount * 100)

    existing = (
        db.query(IncomeAdjustment)
        .filter(
            IncomeAdjustment.income_id == income_id,
            IncomeAdjustment.effective_date == body.effective_date,
        )
        .first()
    )

    if existing:
        existing.actual_amount = actual_cents
        existing.note = body.note
        db.commit()
        db.refresh(existing)
        record = existing
    else:
        record = IncomeAdjustment(
            income_id=income_id,
            effective_date=body.effective_date,
            actual_amount=actual_cents,
            note=body.note,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    return SuccessResponse.of(_to_read(record, income.amount))


@router.get(
    "/incomes/{income_id}/adjustments",
    response_model=SuccessResponse[list[IncomeAdjustmentRead]],
)
def list_income_adjustments(income_id: int, db: Session = Depends(get_db)):
    income = db.get(Income, income_id)
    if not income:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "收入不存在"},
        )
    records = (
        db.query(IncomeAdjustment)
        .filter(IncomeAdjustment.income_id == income_id)
        .order_by(IncomeAdjustment.effective_date)
        .all()
    )
    return SuccessResponse.of([_to_read(r, income.amount) for r in records])


@router.delete(
    "/income-adjustments/{adjustment_id}",
    response_model=SuccessResponse[dict],
)
def delete_income_adjustment(adjustment_id: int, db: Session = Depends(get_db)):
    record = db.get(IncomeAdjustment, adjustment_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Adjustment 不存在"},
        )
    db.delete(record)
    db.commit()
    return SuccessResponse.of({"deleted": adjustment_id})


def _to_read(record: IncomeAdjustment, base_amount_cents: int) -> IncomeAdjustmentRead:
    """delta_amount 於 read 時動態計算，確保事後修改 Income.amount 後仍正確。"""
    return IncomeAdjustmentRead(
        id=record.id,
        income_id=record.income_id,
        effective_date=record.effective_date,
        actual_amount=record.actual_amount / 100,
        delta_amount=(record.actual_amount - base_amount_cents) / 100,
        note=record.note,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
