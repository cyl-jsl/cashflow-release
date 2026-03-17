from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.planning import CanISpendRequest, SpendImpact, SavingsGoalRequest, SavingsGoalResponse
from app.services.planning import evaluate_spend, evaluate_savings_goal

router = APIRouter(prefix="/api/v1/planning", tags=["planning"])


@router.post("/can-i-spend", response_model=SuccessResponse[SpendImpact])
def can_i_spend(
    req: CanISpendRequest,
    db: Session = Depends(get_db),
):
    amount_cents = round(req.amount * 100)

    result = evaluate_spend(
        db,
        amount_cents=amount_cents,
        as_of=req.date,
        until_date=None,  # 預設到月底
    )

    return SuccessResponse.of(SpendImpact(
        available_before=result["available_before"] / 100,
        available_after=result["available_after"] / 100,
        period=result["period"],
        is_feasible=result["is_feasible"],
        summary=result["summary"],
    ))


@router.post("/savings-goal", response_model=SuccessResponse[SavingsGoalResponse])
def savings_goal(
    req: SavingsGoalRequest,
    db: Session = Depends(get_db),
):
    target_cents = round(req.target_amount * 100)
    monthly_saving_cents = round(req.monthly_saving * 100) if req.monthly_saving else None

    result = evaluate_savings_goal(
        db,
        target_amount_cents=target_cents,
        monthly_saving_cents=monthly_saving_cents,
        target_date=req.target_date,
    )

    return SuccessResponse.of(SavingsGoalResponse(
        monthly_surplus=result["monthly_surplus"] / 100,
        monthly_needed=result.get("monthly_needed", 0) / 100 if result.get("monthly_needed") else None,
        months_to_target=result.get("months_to_target"),
        months_needed=result.get("months_needed"),
        projected_date=result.get("projected_date"),
        target_date=result.get("target_date"),
        is_feasible=result["is_feasible"],
        summary=result["summary"],
    ))
