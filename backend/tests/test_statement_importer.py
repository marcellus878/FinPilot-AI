from datetime import datetime
from decimal import Decimal
import io
import unittest
import uuid

from fastapi.testclient import TestClient
import openpyxl
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.financial_engine.statement_importer import (
    generate_transaction_fingerprint,
    process_statement_file,
)
from app.main import app
from tests.test_helpers import create_test_env


class StatementImporterTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.TestingSessionLocal, cls.test_user, cls.client = create_test_env(app, "statement_test@finpilot.ai")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def test_01_csv_statement_parsing_and_categorization(self):
        csv_data = """Date,Narration,Debit,Credit,Balance
2026-03-01,SALARY CREDIT FROM ACME CORP,,5000.00,5000.00
2026-03-02,SWIGGY BANGALORE,450.00,,4550.00
2026-03-03,UBER TRIP BANGALORE,280.00,,4270.00
2026-03-04,NETFLIX SUBSCRIPTION,199.00,,4071.00
2026-03-05,AIRTEL FIBER BROADBAND,1199.00,,2872.00
"""
        preview = process_statement_file(
            file_bytes=csv_data.encode("utf-8"),
            filename="hdfc_bank_statement.csv",
        )

        self.assertEqual(preview.total_rows, 5)
        self.assertEqual(preview.valid_count, 5)
        self.assertEqual(preview.duplicate_count, 0)
        self.assertEqual(preview.skipped_count, 0)

        # Check categorization
        cats = [t.category for t in preview.transactions if t.is_valid]
        self.assertIn("Salary/Income", cats)
        self.assertIn("Food", cats)
        self.assertIn("Transport", cats)
        self.assertIn("Entertainment", cats)
        self.assertIn("Bills & Utilities", cats)

    def test_02_xlsx_statement_parsing(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Txn Date", "Particulars", "Amount", "Type"])
        ws.append(["2026-03-10", "Amazon India Marketplace", 1299.00, "Debit"])
        ws.append(["2026-03-11", "Freelance Consulting Fee", 15000.00, "Credit"])

        bio = io.BytesIO()
        wb.save(bio)
        bio.seek(0)

        preview = process_statement_file(
            file_bytes=bio.getvalue(),
            filename="statement.xlsx",
        )

        self.assertEqual(preview.total_rows, 2)
        self.assertEqual(preview.valid_count, 2)
        self.assertEqual(preview.file_type, "xlsx")
        self.assertEqual(preview.transactions[0].category, "Shopping")
        self.assertEqual(preview.transactions[1].type, "income")

    def test_03_duplicate_detection_intra_file(self):
        csv_data = """Date,Description,Debit,Credit
2026-03-01,SWIGGY BANGALORE,450.00,
2026-03-01,SWIGGY BANGALORE,450.00,
"""
        preview = process_statement_file(
            file_bytes=csv_data.encode("utf-8"),
            filename="duplicates.csv",
        )

        self.assertEqual(preview.total_rows, 2)
        self.assertEqual(preview.valid_count, 1)
        self.assertEqual(preview.duplicate_count, 1)
        self.assertTrue(preview.transactions[1].is_duplicate)

    def test_04_malformed_rows_skipped(self):
        csv_data = """Date,Description,Debit,Credit
INVALID_DATE,Some purchase,100.00,
2026-03-02,Missing amount,,
2026-03-03,Valid purchase,50.00,
"""
        preview = process_statement_file(
            file_bytes=csv_data.encode("utf-8"),
            filename="malformed.csv",
        )

        self.assertEqual(preview.total_rows, 3)
        self.assertEqual(preview.valid_count, 1)
        self.assertEqual(preview.skipped_count, 2)

    def test_05_api_statement_preview_and_confirm(self):
        csv_data = """Date,Narration,Debit,Credit
2026-03-12,BLINKIT GROCERY,650.00,
2026-03-13,STARBUCKS COFFEE,320.00,
"""
        files = {"file": ("bank.csv", csv_data.encode("utf-8"), "text/csv")}
        res_prev = self.client.post("/api/v1/transactions/import/preview", files=files)
        self.assertEqual(res_prev.status_code, 200)
        data_prev = res_prev.json()
        self.assertEqual(data_prev["valid_count"], 2)

        # Confirm import
        confirm_payload = {
            "transactions": [
                {
                    "transaction_date": t["transaction_date"],
                    "amount": t["amount"],
                    "type": t["type"],
                    "category": t["category"],
                    "description": t["description"],
                    "fingerprint": t["fingerprint"],
                }
                for t in data_prev["transactions"]
                if t["is_valid"]
            ]
        }
        res_conf = self.client.post("/api/v1/transactions/import/confirm", json=confirm_payload)
        self.assertEqual(res_conf.status_code, 201)
        self.assertEqual(res_conf.json()["imported_count"], 2)


if __name__ == "__main__":
    unittest.main()
