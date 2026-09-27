import unittest
from datetime import date, timedelta
from decimal import Decimal

from app.financial_engine import (
    allocate_goals_conflict,
    calculate_budget_variance,
    calculate_debt_to_income_ratio,
    calculate_disposable_income,
    calculate_emergency_fund_status,
    calculate_expense_ratio,
    calculate_financial_health_score,
    calculate_goal_completion_timeline,
    calculate_required_goal_contribution,
    calculate_savings_rate,
    evaluate_purchase_affordability,
    quantize_currency,
    simulate_scenario_impact,
    to_decimal,
)


class FinancialEngineTestCase(unittest.TestCase):
    # 1. Disposable Income
    def test_disposable_income_normal(self):
        # 5000 income - 2500 expenses - 500 debt - 200 other = 1800
        result = calculate_disposable_income(
            monthly_income="5000.00",
            essential_expenses="2500.00",
            monthly_debt_payments="500.00",
            other_discretionary_expenses="200.00",
        )
        self.assertEqual(result, Decimal("1800.00"))

    def test_disposable_income_zero_expenses_debt(self):
        result = calculate_disposable_income(
            monthly_income=4000,
            essential_expenses=0,
            monthly_debt_payments=0,
        )
        self.assertEqual(result, Decimal("4000.00"))

    def test_disposable_income_negative_result(self):
        # Expenses exceed income -> negative disposable
        result = calculate_disposable_income(
            monthly_income=2000,
            essential_expenses=2500,
            monthly_debt_payments=500,
        )
        self.assertEqual(result, Decimal("-1000.00"))

    def test_disposable_income_invalid_negative_input(self):
        with self.assertRaises(ValueError):
            calculate_disposable_income(
                monthly_income="-5000",
                essential_expenses="2000",
            )

    # 2. Savings Rate
    def test_savings_rate_normal(self):
        # 1000 savings / 5000 income = 20%
        rate = calculate_savings_rate(1000, 5000)
        self.assertEqual(rate, Decimal("20.00"))

    def test_savings_rate_zero_income(self):
        rate = calculate_savings_rate(500, 0)
        self.assertEqual(rate, Decimal("0.00"))

    def test_savings_rate_negative_savings(self):
        rate = calculate_savings_rate(-500, 5000)
        self.assertEqual(rate, Decimal("-10.00"))

    # 3. Expense Ratio
    def test_expense_ratio_normal(self):
        # 2500 / 5000 = 50%
        ratio = calculate_expense_ratio(2500, 5000)
        self.assertEqual(ratio, Decimal("50.00"))

    def test_expense_ratio_zero_income(self):
        ratio = calculate_expense_ratio(2500, 0)
        self.assertEqual(ratio, Decimal("100.00"))
        ratio_zero = calculate_expense_ratio(0, 0)
        self.assertEqual(ratio_zero, Decimal("0.00"))

    # 4. Debt-to-Income (DTI)
    def test_dti_ratio_normal(self):
        # 1000 / 5000 = 20%
        dti = calculate_debt_to_income_ratio(1000, 5000)
        self.assertEqual(dti, Decimal("20.00"))

    def test_dti_ratio_zero_debt(self):
        dti = calculate_debt_to_income_ratio(0, 5000)
        self.assertEqual(dti, Decimal("0.00"))

    def test_dti_ratio_zero_income(self):
        dti = calculate_debt_to_income_ratio(500, 0)
        self.assertEqual(dti, Decimal("100.00"))

    # 5. Budget Variance
    def test_budget_variance_expense_unfavorable(self):
        # Actual 600 vs Budget 500 -> +100 unfavorable
        res = calculate_budget_variance(600, 500, is_income_category=False)
        self.assertEqual(res.variance, Decimal("100.00"))
        self.assertEqual(res.variance_percentage, Decimal("20.00"))
        self.assertEqual(res.status, "unfavorable")
        self.assertTrue(res.is_over_budget)

    def test_budget_variance_expense_favorable(self):
        # Actual 400 vs Budget 500 -> -100 favorable
        res = calculate_budget_variance(400, 500, is_income_category=False)
        self.assertEqual(res.variance, Decimal("-100.00"))
        self.assertEqual(res.status, "favorable")
        self.assertFalse(res.is_over_budget)

    def test_budget_variance_income_favorable(self):
        # Income Actual 5500 vs Budget 5000 -> favorable
        res = calculate_budget_variance(5500, 5000, is_income_category=True)
        self.assertEqual(res.status, "favorable")

    # 6. Emergency Fund Status
    def test_emergency_fund_normal_adequate(self):
        # 15000 savings, 3000 essential expenses -> 5 months runway (target 6 months = 18000)
        res = calculate_emergency_fund_status(
            emergency_savings="15000.00",
            monthly_essential_expenses="3000.00",
            target_months=6,
        )
        self.assertEqual(res.months_covered, Decimal("5.00"))
        self.assertEqual(res.shortfall, Decimal("3000.00"))
        self.assertEqual(res.surplus, Decimal("0.00"))
        self.assertTrue(res.is_adequate)  # >= 3 months is adequate
        self.assertEqual(res.status_label, "adequate")

    def test_emergency_fund_optimal(self):
        # 24000 savings, 3000 expenses -> 8 months runway (surplus 6000)
        res = calculate_emergency_fund_status(
            emergency_savings=24000,
            monthly_essential_expenses=3000,
            target_months=6,
        )
        self.assertEqual(res.months_covered, Decimal("8.00"))
        self.assertEqual(res.surplus, Decimal("6000.00"))
        self.assertEqual(res.shortfall, Decimal("0.00"))
        self.assertEqual(res.status_label, "optimal")

    def test_emergency_fund_critical(self):
        # 1000 savings, 3000 expenses -> 0.33 months runway
        res = calculate_emergency_fund_status(1000, 3000)
        self.assertEqual(res.status_label, "critical")
        self.assertFalse(res.is_adequate)

    def test_emergency_fund_zero_expenses(self):
        res = calculate_emergency_fund_status(5000, 0)
        self.assertTrue(res.is_adequate)
        self.assertEqual(res.status_label, "optimal")

    # 7. Required Goal Contribution
    def test_required_goal_contribution_normal(self):
        today = date(2026, 1, 1)
        target_date = date(2026, 11, 1)  # 10 months away
        # Target: 10000, Current: 2000 -> Remaining: 8000 / 10 = 800.00/mo
        res = calculate_required_goal_contribution(
            target_amount=10000,
            current_amount=2000,
            target_date=target_date,
            current_date=today,
            monthly_disposable_income=1000,
        )
        self.assertEqual(res.remaining_amount, Decimal("8000.00"))
        self.assertEqual(res.months_remaining, 10)
        self.assertEqual(res.required_monthly_contribution, Decimal("800.00"))
        self.assertTrue(res.is_feasible)
        self.assertFalse(res.is_completed)

    def test_required_goal_contribution_already_completed(self):
        res = calculate_required_goal_contribution(
            target_amount=5000,
            current_amount=5000,
            target_date="2027-12-31",
        )
        self.assertTrue(res.is_completed)
        self.assertEqual(res.required_monthly_contribution, Decimal("0.00"))

    def test_required_goal_contribution_impossible_deadline(self):
        today = date(2026, 5, 1)
        target_date = date(2026, 4, 1)  # in the past
        res = calculate_required_goal_contribution(
            target_amount=5000,
            current_amount=1000,
            target_date=target_date,
            current_date=today,
        )
        self.assertFalse(res.is_feasible)
        self.assertEqual(res.status, "unfeasible_deadline")

    def test_required_goal_contribution_underfunded(self):
        today = date(2026, 1, 1)
        target_date = date(2026, 5, 1)  # 4 months
        # Remaining 4000 / 4 = 1000/mo, disposable income is only 600/mo
        res = calculate_required_goal_contribution(
            target_amount=5000,
            current_amount=1000,
            target_date=target_date,
            current_date=today,
            monthly_disposable_income=600,
        )
        self.assertFalse(res.is_feasible)
        self.assertEqual(res.status, "underfunded")

    # 8. Goal Timeline
    def test_goal_completion_timeline_normal(self):
        # Target 12000, Current 2000, Monthly 1000 -> 10000 / 1000 = 10 months
        res = calculate_goal_completion_timeline(12000, 2000, 1000)
        self.assertEqual(res.months_to_complete, 10)
        self.assertTrue(res.is_achievable)

    def test_goal_completion_timeline_zero_contribution(self):
        res = calculate_goal_completion_timeline(10000, 2000, 0)
        self.assertFalse(res.is_achievable)
        self.assertEqual(res.months_to_complete, -1)

    # 9. Purchase Affordability
    def test_purchase_affordability_safe(self):
        # Savings: 25000, Expenses: 3000 (EF 6mo = 18000). Purchase: 3000 -> leaves 22000 (safe)
        res = evaluate_purchase_affordability(
            purchase_amount=3000,
            current_savings=25000,
            monthly_income=6000,
            monthly_essential_expenses=3000,
            monthly_debt_payments=500,
        )
        self.assertTrue(res.is_affordable)
        self.assertEqual(res.affordability_grade, "safe")
        self.assertEqual(res.new_savings_balance, Decimal("22000.00"))

    def test_purchase_affordability_exceeds_savings(self):
        res = evaluate_purchase_affordability(
            purchase_amount=15000,
            current_savings=10000,
            monthly_income=5000,
            monthly_essential_expenses=2500,
        )
        self.assertFalse(res.is_affordable)
        self.assertEqual(res.affordability_grade, "unaffordable")
        self.assertEqual(res.shortfall, Decimal("5000.00"))

    def test_purchase_affordability_depletes_emergency_fund(self):
        # Savings: 10000, Expenses: 3000 (3mo EF = 9000). Purchase: 6000 -> leaves 4000 (1.33 mo, critical)
        res = evaluate_purchase_affordability(
            purchase_amount=6000,
            current_savings=10000,
            monthly_income=5000,
            monthly_essential_expenses=3000,
        )
        self.assertFalse(res.is_affordable)
        self.assertEqual(res.affordability_grade, "unaffordable")

    # 10. Scenario Simulation
    def test_scenario_income_decrease(self):
        res = simulate_scenario_impact(
            monthly_income=6000,
            monthly_essential_expenses=3000,
            monthly_debt_payments=1000,
            current_savings=15000,
            scenario_type="income_change",
            change_amount=-1500,  # Income drops to 4500
            active_goals=[{
                "id": "g1",
                "name": "Vacation",
                "target_amount": 5000,
                "current_amount": 1000,
                "monthly_contribution": 500,
            }],
        )
        self.assertEqual(res.new_disposable_income, Decimal("500.00"))
        self.assertEqual(res.disposable_income_delta, Decimal("-1500.00"))
        self.assertTrue(res.is_sustainable)
        self.assertEqual(len(res.goal_timeline_impacts), 1)

    # 11. Financial Health Score
    def test_financial_health_score_excellent(self):
        # High income, low debt, strong savings, high emergency coverage
        res = calculate_financial_health_score(
            monthly_income=10000,
            essential_expenses=3000,
            monthly_debt_payments=500,
            current_savings=30000,
        )
        self.assertGreaterEqual(res.overall_score, Decimal("85.00"))
        self.assertEqual(res.grade, "Excellent")

    def test_financial_health_score_critical(self):
        # Zero income, high debt, zero savings
        res = calculate_financial_health_score(
            monthly_income=0,
            essential_expenses=2000,
            monthly_debt_payments=1500,
            current_savings=0,
        )
        self.assertLess(res.overall_score, Decimal("40.00"))
        self.assertEqual(res.grade, "Critical")

    # 12. Goal Conflict Allocation
    def test_goal_conflict_allocation_priority_waterfall(self):
        goals = [
            {"id": "g1", "name": "Emergency Fund", "priority": "high", "required_monthly": 500, "target_amount": 10000},
            {"id": "g2", "name": "Debt Payoff", "priority": "high", "required_monthly": 300, "target_amount": 5000},
            {"id": "g3", "name": "Vacation", "priority": "medium", "required_monthly": 400, "target_amount": 4000},
            {"id": "g4", "name": "New Gadget", "priority": "low", "required_monthly": 200, "target_amount": 1000},
        ]
        # Available funds: $1000
        # High tier requires 500 + 300 = 800 (Funded in full).
        # Remaining for Medium tier: 200 (Medium requires 400 -> gets 200, partial).
        # Low tier gets 0 (unfunded).
        res = allocate_goals_conflict(goals, available_monthly_funds=1000)
        self.assertEqual(res.total_allocated, Decimal("1000.00"))
        self.assertEqual(res.remaining_unallocated, Decimal("0.00"))
        self.assertEqual(res.fully_funded_count, 2)
        self.assertEqual(res.partially_funded_count, 1)
        self.assertEqual(res.unfunded_count, 1)

        alloc_map = {a.goal_id: a.allocated_amount for a in res.allocations}
        self.assertEqual(alloc_map["g1"], Decimal("500.00"))
        self.assertEqual(alloc_map["g2"], Decimal("300.00"))
        self.assertEqual(alloc_map["g3"], Decimal("200.00"))
        self.assertEqual(alloc_map["g4"], Decimal("0.00"))

    def test_goal_conflict_allocation_zero_funds(self):
        goals = [
            {"id": "g1", "name": "Retirement", "priority": "high", "required_monthly": 500},
        ]
        res = allocate_goals_conflict(goals, available_monthly_funds=0)
        self.assertEqual(res.total_allocated, Decimal("0.00"))
        self.assertEqual(res.unfunded_count, 1)


if __name__ == "__main__":
    unittest.main()
