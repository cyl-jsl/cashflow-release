from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import Transaction
from app.models.credit_card import CreditCard
from app.models.account import Account
from app.schemas.transaction import TransactionRead, ImportResponse, to_read
from app.schemas.common import SuccessResponse
from app.services.csv_import import parse_csv, parse_xlsx

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.get("", response_model=SuccessResponse[list[TransactionRead]])
def list_transactions(
    credit_card_id: int | None = Query(None),
    account_id: int | None = Query(None),
    source_file: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Transaction).order_by(Transaction.date.desc())
    if credit_card_id is not None:
        query = query.filter(Transaction.credit_card_id == credit_card_id)
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)
    if source_file is not None:
        query = query.filter(Transaction.source_file == source_file)
    txns = query.all()
    return SuccessResponse.of([to_read(t) for t in txns])


@router.post("/import", response_model=SuccessResponse[ImportResponse])
async def import_transactions(
    file: UploadFile = File(...),
    date_column: str = Form("date"),
    description_column: str = Form("description"),
    amount_column: str = Form("amount"),
    credit_card_id: int | None = Form(None),
    account_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    # Validate references
    if credit_card_id is not None:
        card = db.query(CreditCard).filter(CreditCard.id == credit_card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "信用卡不存在"})
    if account_id is not None:
        acct = db.query(Account).filter(Account.id == account_id).first()
        if not acct:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "帳戶不存在"})

    data = await file.read()
    filename = file.filename or "unknown"

    try:
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            parsed = parse_xlsx(data, date_column, description_column, amount_column)
        else:
            parsed = parse_csv(data, date_column, description_column, amount_column)
    except ValueError as e:
        raise HTTPException(status_code=422, detail={"code": "VALIDATION_ERROR", "message": str(e)})

    total_spending_cents = 0
    for item in parsed:
        txn = Transaction(
            date=item["date"],
            description=item["description"],
            amount=item["amount_cents"],
            credit_card_id=credit_card_id,
            account_id=account_id,
            source_file=filename,
        )
        db.add(txn)
        if item["amount_cents"] > 0:
            total_spending_cents += item["amount_cents"]

    db.commit()

    return SuccessResponse.of(ImportResponse(
        transactions_created=len(parsed),
        total_spending=total_spending_cents / 100,
        source_file=filename,
        credit_card_id=credit_card_id,
    ))


@router.delete("", response_model=SuccessResponse[dict])
def delete_transactions(
    source_file: str = Query(..., description="必須指定要刪除的匯入批次檔名"),
    db: Session = Depends(get_db),
):
    query = db.query(Transaction).filter(Transaction.source_file == source_file)
    count = query.count()
    if count == 0:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": f"找不到來源檔案：{source_file}"})
    query.delete(synchronize_session=False)
    db.commit()
    return SuccessResponse.of({"deleted": count})
