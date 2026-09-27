from decimal import Decimal
import unittest

from app.financial_engine.scenarios import (
    compare_decision_scenarios,
    simulate_detailed_decision_scenario,
)


class ScenarioSimulatorTestCase(unittest.TestCase):
    def setUp(self):
        self.income = Decimal("5000.00")
        self.expenses = Decimal("2500.00")
        self.debt = Decimal("500.00")
        self.savings = Decimal("15000.00")
        self.active_goals = [
            {
                "id": "g1",
                "name": "Emergency Cushion",
                "target_amount": Decimal("10000.00"),
                "current_amount": Decimal("5000.00"),
                "monthly_contribution": Decimal("500.00"),
            }
        ]

    def test_01_one_time_purchase_simulation(self):
        res = simulate_detailed_decision_scenario(
            monthly_income=self.income,
            monthly_essential_expenses=self.expenses,
            monthly_debt_payments=self.debt,
            current_savings=self.savings,
            scenario_type="one_time_purchase",
            amount=Decimal("2000.00"),
            scenario_name="Buy High-End Laptop",
            active_goals=self.active_goals,
        )
        self.assertEqual(res.before_state.current_savings, Decimal("15000.00"))
        self.assertEqual(res.after_state.current_savings, Decimal("13000.00"))
        self.assertEqual(res.delta.savings_delta, Decimal("-2000.00"))
        self.assertEqual(res.delta.monthly_disposable_income_delta, Decimal("0.00"))
        self.assertTrue(res.is_sustainable)
        self.assertEqual(res.affordability_verdict, "safe")

    def test_02_delayed_purchase_simulation(self):
        res = simulate_detailed_decision_scenario(
            monthly_income=self.income,
            monthly_essential_expenses=self.expenses,
            monthly_debt_payments=self.debt,
            current_savings=self.savings,
            scenario_type="one_time_purchase",
            amount=Decimal("2000.00"),
            timing_months=3,
            scenario_name="Delayed Laptop Purchase",
        )
        # With 3 months delay, disposable income of $2000/mo allows accumulating additional savings before purchase
        self.assertTrue(res.is_sustainable)
        self.assertEqual(res.timing_months, 3)

    def test_03_new_recurring_expense_simulation(self):
        res = simulate_detailed_decision_scenario(
            monthly_income=self.income,
            monthly_essential_expenses=self.expenses,
            monthly_debt_payments=self.debt,
            current_savings=self.savings,
            scenario_type="new_recurring_expense",
            amount=Decimal("400.00"),
            scenario_name="New Car Lease",
            active_goals=self.active_goals,
        )
        self.assertEqual(res.before_state.monthly_essential_expenses, Decimal("2500.00"))
        self.assertEqual(res.after_state.monthly_essential_expenses, Decimal("2900.00"))
        self.assertEqual(res.before_state.monthly_disposable_income, Decimal("2000.00"))
        self.assertEqual(res.after_state.monthly_disposable_income, Decimal("1600.00"))
        self.assertEqual(res.delta.monthly_disposable_income_delta, Decimal("-400.00"))
        self.assertTrue(res.is_sustainable)

    def test_04_income_change_simulation(self):
        # 1. Income raise of $1,000
        res_raise = simulate_detailed_decision_scenario(
            monthly_income=self.income,
            monthly_essential_expenses=self.expenses,
            monthly_debt_payments=self.debt,
            current_savings=self.savings,
            scenario_type="income_change",
            amount=Decimal("1000.00"),
            scenario_name="Promotion Raise",
        )
        self.assertEqual(res_raise.after_state.monthly_income, Decimal("6000.00"))
        self.assertEqual(res_raise.after_state.monthly_disposable_income, Decimal("3000.00"))

        # 2. Income cut of -$1,000
        res_cut = simulate_detailed_decision_scenario(
            monthly_income=self.income,
            monthly_essential_expenses=self.expenses,
            monthly_debt_payments=self.debt,
            current_savings=self.savings,
            scenario_type="income_change",
            amount=Decimal("-1000.00"),
            scenario_name="Pay Cut",
        )
        self.assertEqual(res_cut.after_state.monthly_income, Decimal("4000.00"))
        self.assertEqual(res_cut.after_state.monthly_disposable_income, Decimal("1000.00"))

    def test_05_unexpected_expense_exceeding_savings(self):
        res = simulate_detailed_decision_scenario(
            monthly_income=self.income,
            monthly_essential_expenses=self.expenses,
            monthly_debt_payments=self.debt,
            current_savings=Decimal("3000.00"),
            scenario_type="unexpected_expense",
            amount=Decimal("10000.00"),
            scenario_name="Major Emergency",
        )
        self.assertEqual(res.after_state.current_savings, Decimal("0.00"))
        self.assertEqual(res.affordability_verdict, "unaffordable")
        self.assertTrue(len(res.warnings) > 0)

    def test_06_compare_multiple_scenarios(self):
        scenarios = [
            {"id": "sc_a", "name": "Scenario A: Buy ₹80k laptop now", "type": "one_time_purchase", "amount": Decimal("1000.00"), "timing_months": 0},
            {"id": "sc_b", "name": "Scenario B: Buy ₹55k laptop", "type": "one_time_purchase", "amount": Decimal("700.00"), "timing_months": 0},
            {"id": "sc_c", "name": "Scenario C: Buy ₹80k laptop after 3 months", "type": "one_time_purchase", "amount": Decimal("1000.00"), "timing_months": 3},
        ]

        comp = compare_decision_scenarios(
            monthly_income=self.income,
            monthly_essential_expenses=self.expenses,
            monthly_debt_payments=self.debt,
            current_savings=self.savings,
            scenarios_list=scenarios,
            active_goals=self.active_goals,
        )

        self.assertEqual(len(comp.scenarios), 3)
        self.assertEqual(len(comp.tradeoff_summary), 3)
        self.assertEqual(comp.baseline.current_savings, Decimal("15000.00"))


if __name__ == "__main__":
    unittest.main()
