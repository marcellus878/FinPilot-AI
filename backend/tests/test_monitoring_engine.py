from decimal import Decimal
import unittest

from app.financial_engine.monitoring import (
    FinancialChangeItem,
    MonitoringSnapshot,
    ReplanningAssessment,
    build_monitoring_snapshot,
    detect_financial_changes,
    evaluate_replanning_triggers,
    generate_adaptive_replanning_strategies,
    generate_plan_comparison,
)


class MonitoringEngineTestCase(unittest.TestCase):
    def setUp(self):
        self.baseline = build_monitoring_snapshot(
            monthly_income=Decimal("6000.00"),
            essential_expenses=Decimal("2500.00"),
            discretionary_expenses=Decimal("900.00"),
            current_savings=Decimal("15000.00"),
            monthly_debt=Decimal("300.00"),
            safe_to_spend_daily=Decimal("38.33"),
            emergency_runway_months=Decimal("6.00"),
            emergency_runway_status="adequate",
            financial_health_score=Decimal("82.00"),
            financial_health_grade="A",
            budget_variance=Decimal("0.00"),
            recurring_commitments_monthly=Decimal("400.00"),
            active_goals_count=2,
            goals_monthly_required=Decimal("1000.00"),
            goals_monthly_capacity=Decimal("2000.00"),
            goals_feasible=True,
        )

    def test_01_build_snapshot_and_quantization(self):
        snap = self.baseline
        self.assertEqual(snap.monthly_income, Decimal("6000.00"))
        self.assertEqual(snap.monthly_essential_expenses, Decimal("2500.00"))
        self.assertEqual(snap.monthly_total_expenses, Decimal("3400.00"))
        self.assertEqual(snap.savings_rate, Decimal("53.33"))
        self.assertTrue(snap.goals_feasible)

    def test_02_detect_income_and_spending_changes(self):
        current = build_monitoring_snapshot(
            monthly_income=Decimal("5000.00"),  # $1,000 drop (-16.67%)
            essential_expenses=Decimal("2800.00"),  # $300 increase (+12%)
            discretionary_expenses=Decimal("1400.00"),  # $500 surge (+55.56%)
            current_savings=Decimal("12000.00"),
            monthly_debt=Decimal("300.00"),
            safe_to_spend_daily=Decimal("10.00"),
            emergency_runway_months=Decimal("4.28"),
            emergency_runway_status="adequate",
            financial_health_score=Decimal("68.00"),
            financial_health_grade="B",
            budget_variance=Decimal("-250.00"),  # Overspending
            recurring_commitments_monthly=Decimal("600.00"),  # +$200
            active_goals_count=2,
            goals_monthly_required=Decimal("1000.00"),
            goals_monthly_capacity=Decimal("800.00"),  # Shortfall!
            goals_feasible=False,
        )

        changes = detect_financial_changes(self.baseline, current)
        metrics = [c.metric for c in changes]

        self.assertIn("income", metrics)
        self.assertIn("essential_expenses", metrics)
        self.assertIn("discretionary_expenses", metrics)
        self.assertIn("recurring_commitments", metrics)
        self.assertIn("safe_to_spend", metrics)
        self.assertIn("budget_variance", metrics)
        self.assertIn("goal_contribution", metrics)

        income_ch = next(c for c in changes if c.metric == "income")
        self.assertEqual(income_ch.absolute_change, Decimal("-1000.00"))
        self.assertEqual(income_ch.severity, "critical")

        disc_ch = next(c for c in changes if c.metric == "discretionary_expenses")
        self.assertEqual(disc_ch.severity, "high")

    def test_03_evaluate_replanning_triggers_nominal(self):
        # Current state with only minor variations
        nominal_current = build_monitoring_snapshot(
            monthly_income=Decimal("6000.00"),
            essential_expenses=Decimal("2510.00"),
            discretionary_expenses=Decimal("910.00"),
            current_savings=Decimal("15200.00"),
            monthly_debt=Decimal("300.00"),
            safe_to_spend_daily=Decimal("38.00"),
            emergency_runway_months=Decimal("6.05"),
            financial_health_score=Decimal("82.00"),
            recurring_commitments_monthly=Decimal("400.00"),
            goals_monthly_required=Decimal("1000.00"),
            goals_monthly_capacity=Decimal("2000.00"),
            goals_feasible=True,
        )

        changes = detect_financial_changes(self.baseline, nominal_current)
        assessment = evaluate_replanning_triggers(changes, nominal_current, self.baseline)

        self.assertFalse(assessment.replanning_required)
        self.assertEqual(assessment.trigger, "nominal")
        self.assertEqual(assessment.severity, "low")

    def test_04_evaluate_replanning_triggers_activated(self):
        critical_current = build_monitoring_snapshot(
            monthly_income=Decimal("4500.00"),  # Material income reduction
            essential_expenses=Decimal("2700.00"),
            discretionary_expenses=Decimal("1200.00"),
            current_savings=Decimal("6000.00"),  # Depleted emergency runway
            monthly_debt=Decimal("300.00"),
            safe_to_spend_daily=Decimal("0.00"),  # Depleted safe spend
            emergency_runway_months=Decimal("2.22"),  # < 3.0 mos
            emergency_runway_status="vulnerable",
            financial_health_score=Decimal("54.00"),
            financial_health_grade="C",
            budget_variance=Decimal("-350.00"),
            recurring_commitments_monthly=Decimal("650.00"),
            active_goals_count=2,
            goals_monthly_required=Decimal("1000.00"),
            goals_monthly_capacity=Decimal("400.00"),  # Major deficit
            goals_feasible=False,
        )

        changes = detect_financial_changes(self.baseline, critical_current)
        assessment = evaluate_replanning_triggers(changes, critical_current, self.baseline)

        self.assertTrue(assessment.replanning_required)
        self.assertIn(assessment.severity, ["critical", "high"])
        self.assertTrue(len(assessment.affected_areas) >= 2)
        self.assertTrue(len(assessment.reasons) >= 1)

    def test_05_generate_adaptive_strategies_and_comparison(self):
        critical_current = build_monitoring_snapshot(
            monthly_income=Decimal("5000.00"),
            essential_expenses=Decimal("2600.00"),
            discretionary_expenses=Decimal("1100.00"),
            current_savings=Decimal("8000.00"),
            monthly_debt=Decimal("300.00"),
            safe_to_spend_daily=Decimal("12.00"),
            emergency_runway_months=Decimal("3.07"),
            recurring_commitments_monthly=Decimal("500.00"),
            active_goals_count=1,
            goals_monthly_required=Decimal("800.00"),
            goals_monthly_capacity=Decimal("600.00"),
            goals_feasible=False,
        )

        goals = [
            {
                "name": "House Downpayment",
                "target_amount": Decimal("50000.00"),
                "current_amount": Decimal("5000.00"),
                "monthly_contribution": Decimal("800.00"),
            }
        ]

        strategies = generate_adaptive_replanning_strategies(
            current=critical_current,
            baseline=self.baseline,
            active_goals=goals,
        )

        self.assertEqual(len(strategies), 4)
        strat_titles = [s.title for s in strategies]
        self.assertTrue(any("Protect Goals" in t for t in strat_titles))
        self.assertTrue(any("Balanced" in t for t in strat_titles))
        self.assertTrue(any("Lifestyle" in t for t in strat_titles))
        self.assertTrue(any("Defensive" in t for t in strat_titles))

        # Test Before vs After comparison generation
        comp = generate_plan_comparison(
            baseline=self.baseline,
            proposed_strategy=strategies[0],
            reason="Income decreased and discretionary spending surged",
            active_goals=goals,
        )

        self.assertTrue(len(comp.items) >= 5)
        self.assertTrue(len(comp.affected_goals) >= 1)
        self.assertIn("Proposed adaptation adjusts monthly savings", comp.summary)


if __name__ == "__main__":
    unittest.main()
