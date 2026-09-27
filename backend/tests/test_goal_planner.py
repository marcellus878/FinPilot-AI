from datetime import date
from decimal import Decimal
import unittest

from app.financial_engine.goals import (
    analyze_goal_portfolio,
    calculate_goal_completion_timeline,
    calculate_required_goal_contribution,
    generate_goal_conflict_strategies,
)


class GoalPlannerTestCase(unittest.TestCase):
    def test_01_required_goal_contribution_normal(self):
        # Goal: $12,000, current: $0, target date 12 months in future
        current_d = date(2026, 1, 1)
        target_d = date(2027, 1, 1)
        res = calculate_required_goal_contribution(
            target_amount="12000.00",
            current_amount="0.00",
            target_date=target_d,
            current_date=current_d,
            monthly_disposable_income="1500.00",
        )
        self.assertEqual(res.remaining_amount, Decimal("12000.00"))
        self.assertEqual(res.months_remaining, 12)
        self.assertEqual(res.required_monthly_contribution, Decimal("1000.00"))
        self.assertTrue(res.is_feasible)
        self.assertFalse(res.is_completed)

    def test_02_required_goal_contribution_underfunded_and_infeasible(self):
        # Goal: $10,000 in 2 months -> requires $5,000/mo, but disposable is $1,000/mo
        current_d = date(2026, 1, 1)
        target_d = date(2026, 3, 1)
        res = calculate_required_goal_contribution(
            target_amount="10000.00",
            current_amount="0.00",
            target_date=target_d,
            current_date=current_d,
            monthly_disposable_income="1000.00",
        )
        self.assertEqual(res.required_monthly_contribution, Decimal("5000.00"))
        self.assertFalse(res.is_feasible)
        self.assertEqual(res.status, "underfunded")
        self.assertIn("exceeds monthly disposable income", res.warning_or_error)

    def test_03_goal_completion_timeline(self):
        # Target: $6,000, saved: $1,000, monthly contrib: $500 -> 10 months
        res = calculate_goal_completion_timeline(
            target_amount="6000.00",
            current_amount="1000.00",
            monthly_contribution="500.00",
        )
        self.assertEqual(res.remaining_amount, Decimal("5000.00"))
        self.assertEqual(res.months_to_complete, 10)
        self.assertTrue(res.is_achievable)
        self.assertFalse(res.is_completed)

    def test_04_goal_conflict_detection_and_strategies(self):
        # Available = $1,500
        # Goal A (High): req $1,000
        # Goal B (Medium): req $800
        # Goal C (Low): req $500
        # Total req = $2,300 -> Conflict of $800
        goals = [
            {"id": "g1", "name": "Emergency Fund", "priority": "high", "target_amount": "10000", "current_amount": "2000", "required_monthly": "1000", "status": "in_progress"},
            {"id": "g2", "name": "Laptop", "priority": "medium", "target_amount": "2400", "current_amount": "0", "required_monthly": "800", "status": "in_progress"},
            {"id": "g3", "name": "Vacation", "priority": "low", "target_amount": "3000", "current_amount": "500", "required_monthly": "500", "status": "in_progress"},
        ]

        strategies = generate_goal_conflict_strategies(goals, available_monthly_funds="1500.00")
        self.assertEqual(len(strategies), 3)

        # 1. Waterfall: Goal A gets $1000 (100%), Goal B gets $500 (partially), Goal C gets $0
        waterfall = next(s for s in strategies if s.strategy_id == "priority_waterfall")
        self.assertEqual(waterfall.total_allocated, Decimal("1500.00"))
        self.assertEqual(waterfall.allocations[0].allocated_amount, Decimal("1000.00"))
        self.assertTrue(waterfall.allocations[0].is_fully_funded)
        self.assertEqual(waterfall.allocations[1].allocated_amount, Decimal("500.00"))
        self.assertEqual(waterfall.allocations[2].allocated_amount, Decimal("0.00"))

        # 2. Proportional Share: Distributed proportionally to 1000:800:500 (total 2300)
        prop = next(s for s in strategies if s.strategy_id == "proportional_share")
        self.assertEqual(prop.total_allocated, Decimal("1500.00"))
        self.assertTrue(all(a.allocated_amount > 0 for a in prop.allocations))

        # 3. Equal Split: $1500 / 3 = $500 each
        equal = next(s for s in strategies if s.strategy_id == "equal_split")
        self.assertEqual(equal.total_allocated, Decimal("1500.00"))
        for alloc in equal.allocations:
            self.assertEqual(alloc.allocated_amount, Decimal("500.00"))

    def test_05_analyze_goal_portfolio(self):
        goals = [
            {
                "id": "g1",
                "name": "Emergency Fund",
                "category": "Emergency",
                "priority": "high",
                "status": "in_progress",
                "target_amount": "6000.00",
                "current_amount": "2000.00",
                "target_date": "2026-10-01",
                "monthly_contribution": "500.00",
            },
            {
                "id": "g2",
                "name": "Debt Free",
                "category": "Debt",
                "priority": "high",
                "status": "achieved",
                "target_amount": "5000.00",
                "current_amount": "5000.00",
                "target_date": "2026-05-01",
                "monthly_contribution": "0.00",
            },
        ]

        res = analyze_goal_portfolio(goals, available_monthly_capacity="2000.00", reference_date=date(2026, 4, 1))
        self.assertEqual(res.total_target_amount, Decimal("11000.00"))
        self.assertEqual(res.total_saved_amount, Decimal("7000.00"))
        self.assertEqual(res.active_goals_count, 1)
        self.assertEqual(res.achieved_goals_count, 1)
        self.assertTrue(res.is_portfolio_feasible)
        self.assertFalse(res.conflict_detected)


if __name__ == "__main__":
    unittest.main()
