from datetime import date

import pytest

from app.models.credit_card import CreditCard
from app.models.credit_card_bill import CreditCardBill
from app.services.revolving_interest import calculate_and_carry_forward


class TestRevolvingInterest:
    def _make_card(self, db, rate=0.15):
        card = CreditCard(
            name="測試卡", billing_day=15, due_day=3,
            revolving_interest_rate=rate,
        )
        db.add(card)
        db.commit()
        db.refresh(card)
        return card

    def _make_bill(self, db, card_id, year, month, general_spending_cents, due_date, carried_forward=0):
        bill = CreditCardBill(
            credit_card_id=card_id,
            billing_year=year,
            billing_month=month,
            due_date=due_date,
            general_spending=general_spending_cents,
            carried_forward=carried_forward,
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)
        return bill

    def test_partial_payment_carries_principal_and_interest(self, db):
        """部分繳款應將未繳本金+利息結轉至下期帳單。"""
        card = self._make_card(db, rate=0.15)
        bill = self._make_bill(db, card.id, 2026, 3, 1000000, date(2026, 4, 3))  # 10,000 元

        # 繳 6,000 元 → 未繳 4,000 元
        # 利息 = 4,000 * 0.15 / 12 = 50 元 = 5,000 分
        # carried_forward = 未繳 400,000 + 利息 5,000 = 405,000 分
        result = calculate_and_carry_forward(
            db, bill_id=bill.id, paid_amount_cents=600000
        )

        assert result["unpaid_cents"] == 400000
        assert result["interest_cents"] == 5000
        assert result["carried_forward_cents"] == 405000
        assert result["next_bill_id"] is not None

        # 檢查下期帳單
        next_bill = db.query(CreditCardBill).filter(
            CreditCardBill.id == result["next_bill_id"]
        ).first()
        assert next_bill.carried_forward == 405000  # 4,050 元
        assert next_bill.billing_year == 2026
        assert next_bill.billing_month == 4

    def test_full_payment_no_carryover(self, db):
        """全額繳款不結轉。"""
        card = self._make_card(db, rate=0.15)
        bill = self._make_bill(db, card.id, 2026, 3, 1000000, date(2026, 4, 3))

        result = calculate_and_carry_forward(
            db, bill_id=bill.id, paid_amount_cents=1000000
        )

        assert result["unpaid_cents"] == 0
        assert result["interest_cents"] == 0
        assert result["carried_forward_cents"] == 0
        assert result["next_bill_id"] is None

    def test_no_rate_carries_principal_only(self, db):
        """信用卡未設定利率，結轉未繳本金（利息為 0）。"""
        card = CreditCard(name="無利率卡", billing_day=15, due_day=3)
        db.add(card)
        db.commit()
        db.refresh(card)

        bill = self._make_bill(db, card.id, 2026, 3, 1000000, date(2026, 4, 3))

        result = calculate_and_carry_forward(
            db, bill_id=bill.id, paid_amount_cents=600000
        )

        assert result["unpaid_cents"] == 400000
        assert result["interest_cents"] == 0
        assert result["carried_forward_cents"] == 400000  # 只有本金
        assert result["next_bill_id"] is not None

        next_bill = db.query(CreditCardBill).filter(
            CreditCardBill.id == result["next_bill_id"]
        ).first()
        assert next_bill.carried_forward == 400000

    def test_compounds_across_months(self, db):
        """結轉金額包含在下期 total 中，形成複利效果。"""
        card = self._make_card(db, rate=0.15)
        bill_mar = self._make_bill(db, card.id, 2026, 3, 1000000, date(2026, 4, 3))

        # 3 月：繳 6,000 → 未繳 4,000 → carried_forward = 4,050
        result1 = calculate_and_carry_forward(db, bill_id=bill_mar.id, paid_amount_cents=600000)
        next_bill = db.query(CreditCardBill).filter(CreditCardBill.id == result1["next_bill_id"]).first()

        # 4 月帳單：carried_forward=405,000 + general_spending=0 → total=405,000
        # 繳 0 元 → 未繳 405,000
        # 利息 = 405,000 * 0.15 / 12 = 5,063 分（四捨五入）
        # carried_forward = 405,000 + 5,063 = 410,063
        result2 = calculate_and_carry_forward(db, bill_id=next_bill.id, paid_amount_cents=0)

        assert result2["unpaid_cents"] == 405000
        assert result2["interest_cents"] == 5062  # 405000 * 0.15 / 12 = 5062.5, banker's rounding → 5062
        assert result2["carried_forward_cents"] == 410062

    def test_december_to_january_carryover(self, db):
        """12 月帳單結轉至 1 月（跨年）。"""
        card = self._make_card(db, rate=0.15)
        bill = self._make_bill(db, card.id, 2026, 12, 1000000, date(2027, 1, 3))

        result = calculate_and_carry_forward(db, bill_id=bill.id, paid_amount_cents=600000)

        next_bill = db.query(CreditCardBill).filter(CreditCardBill.id == result["next_bill_id"]).first()
        assert next_bill.billing_year == 2027
        assert next_bill.billing_month == 1
