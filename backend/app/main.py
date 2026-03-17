from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401 — ensures SQLAlchemy metadata is populated
from app.routers import accounts, incomes, obligations, forecast, system, credit_cards, credit_card_bills, dashboard, planning, transactions

app = FastAPI(title="Cashflow Dashboard API", version="0.1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(accounts.router)
app.include_router(incomes.router)
app.include_router(obligations.router)
app.include_router(forecast.router)
app.include_router(system.router)
app.include_router(credit_cards.router)
app.include_router(credit_card_bills.router)
app.include_router(dashboard.router)
app.include_router(planning.router)
app.include_router(transactions.router)


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}
