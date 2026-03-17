from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.income import Income
from app.schemas.income import IncomeCreate, IncomeUpdate, IncomeRead, to_read
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/v1/incomes", tags=["incomes"])


@router.get("", response_model=SuccessResponse[list[IncomeRead]])
def list_incomes(db: Session = Depends(get_db)):
    incomes = db.query(Income).all()
    return SuccessResponse.of([to_read(i) for i in incomes])


@router.post("", response_model=SuccessResponse[IncomeRead])
def create_income(payload: IncomeCreate, db: Session = Depends(get_db)):
    income = Income(
        name=payload.name,
        amount=round(payload.amount * 100),
        frequency=payload.frequency.value,
        start_date=payload.start_date,
        end_date=payload.end_date,
        next_date=payload.next_date,
        note=payload.note,
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    return SuccessResponse.of(to_read(income))


@router.put("/{income_id}", response_model=SuccessResponse[IncomeRead])
def update_income(income_id: int, payload: IncomeUpdate, db: Session = Depends(get_db)):
    income = db.query(Income).filter(Income.id == income_id).first()
    if not income:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "收入不存在"})
    update_data = payload.model_dump(exclude_unset=True)
    if "amount" in update_data and update_data["amount"] is not None:
        update_data["amount"] = round(update_data["amount"] * 100)
    if "frequency" in update_data and update_data["frequency"] is not None:
        update_data["frequency"] = update_data["frequency"].value
    for key, value in update_data.items():
        setattr(income, key, value)
    db.commit()
    db.refresh(income)
    return SuccessResponse.of(to_read(income))


@router.delete("/{income_id}", response_model=SuccessResponse[dict])
def delete_income(income_id: int, db: Session = Depends(get_db)):
    income = db.query(Income).filter(Income.id == income_id).first()
    if not income:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "收入不存在"})
    db.delete(income)
    db.commit()
    return SuccessResponse.of({"deleted": income_id})
