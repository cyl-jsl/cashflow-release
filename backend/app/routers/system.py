from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.account import Account
from app.models.income import Income
from app.models.obligation import Obligation
from app.schemas.common import SuccessResponse
from app.services.cycle_advance import advance_all_cycles

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.post("/advance-cycles", response_model=SuccessResponse[dict])
def advance_cycles(db: Session = Depends(get_db)):
    result = advance_all_cycles(db, as_of=date.today())
    return SuccessResponse.of(result)


@router.get("/backup")
def backup_database():
    db_path = settings.database_url.replace("sqlite:///", "")
    return FileResponse(db_path, filename="cashflow-backup.db", media_type="application/octet-stream")


@router.post("/load-sample-data", response_model=SuccessResponse[dict])
def load_sample_data(db: Session = Depends(get_db)):
    """載入範例資料，方便快速體驗。重複呼叫時跳過。"""
    if db.query(Account).count() > 0:
        return SuccessResponse.of({"message": "資料已存在，跳過載入"})

    # 帳戶
    accounts = [
        Account(name="薪轉帳戶", type="bank", balance=8000000, currency="TWD"),
        Account(name="儲蓄帳戶", type="bank", balance=3000000, currency="TWD"),
        Account(name="現金", type="cash", balance=500000, currency="TWD"),
    ]
    for a in accounts:
        db.add(a)

    # 收入
    incomes = [
        Income(name="薪水", amount=5000000, frequency="monthly",
               start_date=date(2026, 1, 5), next_date=date(2026, 4, 5)),
    ]
    for i in incomes:
        db.add(i)

    # 義務
    obligations = [
        Obligation(name="房租", type="fixed", amount=1200000, frequency="monthly",
                   start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1)),
        Obligation(name="Netflix", type="fixed", amount=39000, frequency="monthly",
                   start_date=date(2026, 1, 15), next_due_date=date(2026, 4, 15)),
        Obligation(name="現金生活費", type="budget", amount=800000, frequency="monthly",
                   start_date=date(2026, 1, 1), next_due_date=date(2026, 4, 1)),
        Obligation(name="年度保險", type="fixed", amount=2400000, frequency="yearly",
                   start_date=date(2026, 7, 1), next_due_date=date(2026, 7, 1)),
    ]
    for o in obligations:
        db.add(o)

    db.commit()
    return SuccessResponse.of({
        "accounts_created": len(accounts),
        "incomes_created": len(incomes),
        "obligations_created": len(obligations),
    })
