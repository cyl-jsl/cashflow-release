from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.credit_card import CreditCard
from app.schemas.credit_card import CreditCardCreate, CreditCardUpdate, CreditCardRead, to_read
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/v1/credit-cards", tags=["credit-cards"])


@router.get("", response_model=SuccessResponse[list[CreditCardRead]])
def list_credit_cards(db: Session = Depends(get_db)):
    cards = db.query(CreditCard).all()
    return SuccessResponse.of([to_read(c) for c in cards])


@router.post("", response_model=SuccessResponse[CreditCardRead])
def create_credit_card(payload: CreditCardCreate, db: Session = Depends(get_db)):
    card = CreditCard(
        name=payload.name,
        billing_day=payload.billing_day,
        due_day=payload.due_day,
        credit_limit=round(payload.credit_limit * 100) if payload.credit_limit is not None else None,
        note=payload.note,
        revolving_interest_rate=payload.revolving_interest_rate,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return SuccessResponse.of(to_read(card))


@router.put("/{card_id}", response_model=SuccessResponse[CreditCardRead])
def update_credit_card(card_id: int, payload: CreditCardUpdate, db: Session = Depends(get_db)):
    card = db.query(CreditCard).filter(CreditCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "信用卡不存在"})
    update_data = payload.model_dump(exclude_unset=True)
    if "credit_limit" in update_data and update_data["credit_limit"] is not None:
        update_data["credit_limit"] = round(update_data["credit_limit"] * 100)
    for key, value in update_data.items():
        setattr(card, key, value)
    db.commit()
    db.refresh(card)
    return SuccessResponse.of(to_read(card))


@router.delete("/{card_id}", response_model=SuccessResponse[dict])
def delete_credit_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(CreditCard).filter(CreditCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "信用卡不存在"})
    db.delete(card)
    db.commit()
    return SuccessResponse.of({"deleted": card_id})
