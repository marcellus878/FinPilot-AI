from datetime import datetime
from decimal import Decimal
import unittest

from app.financial_engine.salary_planner import (
    calculate_monthly_recurring_commitments,
    calculate_safe_to_spend,
    calculate_salary_allocation,
    calculate_salary_cycle_dates,
    calculate_survival_projection,
    normalize_commitment_to_monthly,
)


class DummyCommitment:
    def __init__(self, id, name, category, amount, frequency="monthly", next_expected_date=None, is_active=True):
        self.id = id
        self.name = name
        self.category = category
        self.amount = Decimal(str(amount))
        self.frequency = frequency
        self.next_expected_date = next_expected_date
        self.is_active = is_active
        self.is_confirmed = True


class SalaryPlannerTestCase(unittest.TestCase):
    def test_01_salary_cycle_dates(self):
        # Reference date: 2026-03-15. Expected salary day: 1st of month
        # Since 15 >= 1, current cycle started 2026-03-01, next salary on 2026-04-01
        ref = datetime(2026, 3, 15, 10, 0, 0)
        cycle = calculate_salary_cycle_dates(expected_salary_day=1, reference_date=ref)

        self.assertEqual(cycle.cycle_start_date.strftime("%Y-%m-%d"), "2026-03-01")
        self.assertEqual(cycle.next_salary_date.strftime("%Y-%m-%d"), "2026-04-01")
        self.assertEqual(cycle.days_in_cycle, 31)
        self.assertEqual(cycle.days_elapsed, 14)
        self.assertEqual(cycle.days_remaining, 17)

    def test_02_salary_cycle_dates_before_salary_day(self):
        # Reference date: 2026-03-15. Expected salary day: 25th of month
        # Since 15 < 25, current cycle started 2026-02-25, next salary on 2026-03-25
        ref = datetime(2026, 3, 15, 10, 0, 0)
        cycle = calculate_salary_cycle_dates(expected_salary_day=25, reference_date=ref)

        self.assertEqual(cycle.cycle_start_date.strftime("%Y-%m-%d"), "2026-02-25")
        self.assertEqual(cycle.next_salary_date.strftime("%Y-%m-%d"), "2026-03-25")
        self.assertEqual(cycle.days_remaining, 10)

    def test_03_normalize_commitment_frequencies(self):
        self.assertEqual(normalize_commitment_to_monthly(Decimal("100.00"), "weekly"), Decimal("433.33"))
        self.assertEqual(normalize_commitment_to_monthly(Decimal("300.00"), "quarterly"), Decimal("100.00"))
        self.assertEqual(normalize_commitment_to_monthly(Decimal("1200.00"), "annual"), Decimal("100.00"))
        self.assertEqual(normalize_commitment_to_monthly(Decimal("500.00"), "monthly"), Decimal("500.00"))

    def test_04_calculate_monthly_recurring_commitments(self):
        next_salary = datetime(2026, 4, 1)
        ref = datetime(2026, 3, 15)

        comms = [
            DummyCommitment("1", "Apartment Rent", "Rent/Housing", 1200, "monthly", datetime(2026, 3, 20)),
            DummyCommitment("2", "Airtel Broadband", "Bills & Utilities", 50, "monthly", datetime(2026, 3, 25)),
            DummyCommitment("3", "Annual Insurance", "Bills & Utilities", 600, "annual", datetime(2026, 6, 1)),
        ]

        items, total_monthly, upcoming_due = calculate_monthly_recurring_commitments(
            commitments=comms,
            next_salary_date=next_salary,
            reference_date=ref,
        )

        # Total monthly = 1200 + 50 + (600/12 = 50) = 1300.00
        self.assertEqual(total_monthly, Decimal("1300.00"))
        # Upcoming due in current cycle before 2026-04-01: Rent (Mar 20) + Broadband (Mar 25) = 1250.00
        self.assertEqual(upcoming_due, Decimal("1250.00"))

    def test_05_salary_allocation_feasible(self):
        # Income: 60,000 | Fixed: 20,000 | Essentials: 12,000 | Savings: 15,000 | Disc: 8,000 | Buffer: 5,000
        res = calculate_salary_allocation(
            monthly_income=Decimal("60000.00"),
            fixed_commitments=Decimal("20000.00"),
            essential_allowance=Decimal("12000.00"),
            savings_target=Decimal("15000.00"),
            discretionary_allowance=Decimal("8000.00"),
        )

        self.assertTrue(res.is_feasible)
        self.assertEqual(res.remaining_buffer, Decimal("5000.00"))
        self.assertEqual(res.deficit_amount, Decimal("0.00"))
        self.assertEqual(res.fixed_percentage, Decimal("33.33"))
        self.assertEqual(res.savings_percentage, Decimal("25.00"))

    def test_06_salary_allocation_infeasible_and_alternatives(self):
        # Income: 50,000 | Fixed: 25,000 | Essentials: 15,000 | Savings: 15,000 | Disc: 0
        # Total needed: 55,000 -> Infeasible by 5,000
        res = calculate_salary_allocation(
            monthly_income=Decimal("50000.00"),
            fixed_commitments=Decimal("25000.00"),
            essential_allowance=Decimal("15000.00"),
            savings_target=Decimal("15000.00"),
            discretionary_allowance=Decimal("0.00"),
        )

        self.assertFalse(res.is_feasible)
        self.assertEqual(res.deficit_amount, Decimal("5000.00"))
        self.assertEqual(len(res.alternatives), 3)

    def test_07_safe_to_spend_calculator(self):
        # Available: 30,000 | Upcoming commitments: 10,000 | Remaining essentials: 6,000 | Savings reserve: 8,000 | Days: 6
        # Safe to spend = 30000 - 10000 - 6000 - 8000 = 6,000. Daily = 6000 / 6 = 1,000
        res = calculate_safe_to_spend(
            current_available_funds=Decimal("30000.00"),
            upcoming_commitments=Decimal("10000.00"),
            remaining_essential_allowance=Decimal("6000.00"),
            savings_reserve=Decimal("8000.00"),
            days_remaining=6,
        )

        self.assertEqual(res.safe_to_spend_amount, Decimal("6000.00"))
        self.assertEqual(res.daily_safe_to_spend, Decimal("1000.00"))
        self.assertEqual(res.total_committed_and_reserved, Decimal("24000.00"))

    def test_08_survival_projection_statuses(self):
        # Test Comfortable
        res_comf = calculate_survival_projection(
            current_available_funds=Decimal("10000.00"),
            monthly_income=Decimal("5000.00"),
            recent_average_daily_burn=Decimal("50.00"),
            days_remaining=10,
            upcoming_commitments=Decimal("500.00"),
            remaining_essential_allowance=Decimal("1000.00"),
        )
        self.assertEqual(res_comf.status, "comfortable")
        self.assertEqual(res_comf.projected_end_of_month_balance, Decimal("9000.00"))

        # Test At Risk
        res_risk = calculate_survival_projection(
            current_available_funds=Decimal("1000.00"),
            monthly_income=Decimal("5000.00"),
            recent_average_daily_burn=Decimal("200.00"),
            days_remaining=10,
            upcoming_commitments=Decimal("500.00"),
            remaining_essential_allowance=Decimal("1000.00"),
        )
        self.assertEqual(res_risk.status, "at_risk")
        self.assertLess(res_risk.projected_end_of_month_balance, Decimal("0.00"))


if __name__ == "__main__":
    unittest.main()
