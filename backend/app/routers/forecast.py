import calendar
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.income import Income
from app.schemas.common import SuccessResponse
from app.schemas.forecast import AvailableResponse, PeriodInfo, PeriodType, SimulateRequest, SimulateResponse, TimelinePoint, TimelineResponse
from app.services.forecast import calculate_available, calculate_simulated_timeline, calculate_timeline

router = APIRouter(prefix="/api/v1/forecast", tags=["forecast"])


@router.get("/available", response_model=SuccessResponse[AvailableResponse])
def get_available(
    until: date | None = Query(None),
    period_type: PeriodType | None = Query(None),
    period_value: int | None = Query(None),
    db: Session = Depends(get_db),
):
    today = date.today()

    if until:
        target_date = until
    elif period_type == PeriodType.end_of_month or period_type is None:
        # 預設到月底
        last_day = calendar.monthrange(today.year, today.month)[1]
        target_date = date(today.year, today.month, last_day)
    elif period_type == PeriodType.next_payday:
        monthly_incomes = db.query(Income).filter(Income.frequency == "monthly").all()
        if not monthly_incomes:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "NO_MONTHLY_INCOME", "message": "No monthly income found"}},
            )
        target_date = min(i.next_date for i in monthly_incomes)
    elif period_type == PeriodType.days:
        if not period_value or period_value <= 0:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "INVALID_PERIOD", "message": "period_value must be a positive integer"}},
            )
        target_date = today + timedelta(days=period_value)
    else:
        last_day = calendar.monthrange(today.year, today.month)[1]
        target_date = date(today.year, today.month, last_day)

    result = calculate_available(db, from_date=today, until_date=target_date)

    return SuccessResponse.of(AvailableResponse(
        total_balance=result["total_balance"] / 100,
        period_income=result["period_income"] / 100,
        period_obligations=result["period_obligations"] / 100,
        period_credit_card_bills=result["period_credit_card_bills"] / 100,
        available_amount=result["available_amount"] / 100,
        period=PeriodInfo(**{"from": result["period"]["from"], "until": result["period"]["until"]}),
    ))


@router.get("/timeline", response_model=SuccessResponse[TimelineResponse])
def get_timeline(
    months: int = Query(6, ge=1, le=24),
    granularity: str = Query("monthly"),
    db: Session = Depends(get_db),
):
    raw = calculate_timeline(db, months=months, granularity=granularity)

    points = [
        TimelinePoint(
            date=p["date"],
            balance=p["balance"] / 100,
            income_total=p["income_total"] / 100,
            obligation_total=p["obligation_total"] / 100,
            credit_card_total=p["credit_card_total"] / 100,
            note=p["note"],
        )
        for p in raw
    ]

    return SuccessResponse.of(TimelineResponse(
        timeline=points,
        granularity=granularity,
        months=months,
    ))


@router.post("/simulate", response_model=SuccessResponse[SimulateResponse])
def simulate(
    req: SimulateRequest,
    db: Session = Depends(get_db),
):
    income_cents = round(req.monthly_income_change * 100)
    expense_cents = round(req.monthly_expense_change * 100)

    result = calculate_simulated_timeline(
        db,
        monthly_income_change_cents=income_cents,
        monthly_expense_change_cents=expense_cents,
        months=req.months,
    )

    def to_points(raw: list[dict]) -> list[TimelinePoint]:
        return [
            TimelinePoint(
                date=p["date"],
                balance=p["balance"] / 100,
                income_total=p["income_total"] / 100,
                obligation_total=p["obligation_total"] / 100,
                credit_card_total=p["credit_card_total"] / 100,
                note=p.get("note"),
            )
            for p in raw
        ]

    return SuccessResponse.of(SimulateResponse(
        baseline=to_points(result["baseline"]),
        simulated=to_points(result["simulated"]),
        months=req.months,
    ))
