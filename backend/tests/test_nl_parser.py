from datetime import datetime, timedelta
from decimal import Decimal
import unittest

from app.financial_engine.nl_parser import parse_natural_language_transaction


class NaturalLanguageParserTestCase(unittest.TestCase):
    def setUp(self):
        self.ref_date = datetime(2026, 3, 20, 12, 0, 0)  # Friday

    def test_01_swiggy_dinner_yesterday(self):
        text = "Spent 450 rupees on Swiggy for dinner yesterday."
        parsed = parse_natural_language_transaction(text, reference_date=self.ref_date)

        self.assertEqual(parsed.amount, Decimal("450.00"))
        self.assertEqual(parsed.type, "expense")
        self.assertEqual(parsed.category, "Food")
        self.assertEqual(parsed.essentiality, "discretionary")
        self.assertEqual(parsed.transaction_date.date(), (self.ref_date - timedelta(days=1)).date())
        self.assertGreaterEqual(parsed.confidence, 0.8)
        self.assertEqual(len(parsed.missing_fields), 0)

    def test_02_petrol_today(self):
        text = "Spent 500 on petrol today"
        parsed = parse_natural_language_transaction(text, reference_date=self.ref_date)

        self.assertEqual(parsed.amount, Decimal("500.00"))
        self.assertEqual(parsed.type, "expense")
        self.assertEqual(parsed.category, "Transport")
        self.assertEqual(parsed.essentiality, "essential")
        self.assertEqual(parsed.transaction_date.date(), self.ref_date.date())

    def test_03_broadband_bill(self):
        text = "Paid 1200 for broadband"
        parsed = parse_natural_language_transaction(text, reference_date=self.ref_date)

        self.assertEqual(parsed.amount, Decimal("1200.00"))
        self.assertEqual(parsed.type, "expense")
        self.assertEqual(parsed.category, "Bills & Utilities")
        self.assertEqual(parsed.essentiality, "essential")

    def test_04_salary_income(self):
        text = "Got salary of 60000 yesterday"
        parsed = parse_natural_language_transaction(text, reference_date=self.ref_date)

        self.assertEqual(parsed.amount, Decimal("60000.00"))
        self.assertEqual(parsed.type, "income")
        self.assertEqual(parsed.category, "Salary/Income")
        self.assertEqual(parsed.essentiality, "essential")

    def test_05_weekday_relative_date(self):
        # Ref date is Friday (2026-03-20). "last Saturday" refers to 2026-03-14 (6 days ago)
        text = "Spent 350 on dinner last Saturday"
        parsed = parse_natural_language_transaction(text, reference_date=self.ref_date)

        self.assertEqual(parsed.amount, Decimal("350.00"))
        self.assertEqual(parsed.category, "Food")
        self.assertEqual(parsed.transaction_date.date(), (self.ref_date - timedelta(days=6)).date())

    def test_06_k_suffix_and_currency_symbols(self):
        text = "Paid $1.5k for rent on 2026-03-01"
        parsed = parse_natural_language_transaction(text, reference_date=self.ref_date)

        self.assertEqual(parsed.amount, Decimal("1500.00"))
        self.assertEqual(parsed.category, "Rent/Housing")
        self.assertEqual(parsed.essentiality, "essential")
        self.assertEqual(parsed.transaction_date.strftime("%Y-%m-%d"), "2026-03-01")

    def test_07_missing_amount_handling(self):
        text = "Bought some groceries at Trader Joe"
        parsed = parse_natural_language_transaction(text, reference_date=self.ref_date)

        self.assertIsNone(parsed.amount)
        self.assertIn("amount", parsed.missing_fields)
        self.assertEqual(parsed.category, "Groceries")
        self.assertLess(parsed.confidence, 0.7)


if __name__ == "__main__":
    unittest.main()
