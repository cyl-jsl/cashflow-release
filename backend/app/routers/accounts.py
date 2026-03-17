from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate, AccountRead, BatchUpdateBalances, to_read
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.get("", response_model=SuccessResponse[list[AccountRead]])
def list_accounts(db: Session = Depends(get_db)):
    accounts = db.query(Account).all()
    return SuccessResponse.of([to_read(a) for a in accounts])


@router.post("", response_model=SuccessResponse[AccountRead])
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    account = Account(
        name=payload.name,
        type=payload.type.value,
        balance=round(payload.balance * 100),
        currency=payload.currency,
        note=payload.note,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return SuccessResponse.of(to_read(account))


@router.put("/{account_id}", response_model=SuccessResponse[AccountRead])
def update_account(account_id: int, payload: AccountUpdate, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "帳戶不存在"})
    update_data = payload.model_dump(exclude_unset=True)
    if "balance" in update_data and update_data["balance"] is not None:
        update_data["balance"] = round(update_data["balance"] * 100)
        from datetime import datetime
        account.balance_updated_at = datetime.now()
    if "type" in update_data and update_data["type"] is not None:
        update_data["type"] = update_data["type"].value
    for key, value in update_data.items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return SuccessResponse.of(to_read(account))


@router.delete("/{account_id}", response_model=SuccessResponse[dict])
def delete_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "帳戶不存在"})
    db.delete(account)
    db.commit()
    return SuccessResponse.of({"deleted": account_id})


@router.patch("/batch-update-balances", response_model=SuccessResponse[list[AccountRead]])
def batch_update_balances(payload: BatchUpdateBalances, db: Session = Depends(get_db)):
    from datetime import datetime
    updated = []
    for u in payload.updates:
        account = db.query(Account).filter(Account.id == u.id).first()
        if not account:
            raise HTTPException(status_code=404, detail={
                "code": "NOT_FOUND", "message": f"帳戶 {u.id} 不存在"
            })
        account.balance = round(u.balance * 100)
        account.balance_updated_at = datetime.now()
        updated.append(account)
    db.commit()
    for a in updated:
        db.refresh(a)
    return SuccessResponse.of([to_read(a) for a in updated])
