import csv
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import io
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import openpyxl
from pypdf import PdfReader

from app.financial_engine.categorization import (
    categorize_transaction,
    classify_essentiality,
)

@dataclass
class NormalizedStatementTransaction:
    row_index: int
    transaction_date: datetime
    amount: Decimal
    type: str  # 'expense' | 'income'
    category: str
    description: str
    essentiality: str
    essentiality_reason: str
    fingerprint: str
    is_duplicate: bool = False
    is_valid: bool = True
    error_message: Optional[str] = None


@dataclass
class StatementImportPreviewResult:
    filename: str
    file_type: str
    total_rows: int
    valid_count: int
    duplicate_count: int
    skipped_count: int
    detected_columns: Dict[str, str]
    transactions: List[NormalizedStatementTransaction] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


COLUMN_ALIASES = {
    "date": [
        "date", "txn date", "txndate", "transaction date", "value date",
        "posting date", "booking date", "trans date", "tran date"
    ],
    "description": [
        "description", "narration", "particulars", "details", "remarks",
        "transaction details", "merchant", "payee", "note", "narrative"
    ],
    "amount": [
        "amount", "txn amount", "transaction amount", "amt", "net amount"
    ],
    "debit": [
        "debit", "withdrawal", "dr", "withdrawals", "debit amount", "paid out", "debits"
    ],
    "credit": [
        "credit", "deposit", "cr", "deposits", "credit amount", "paid in", "credits"
    ],
    "type": [
        "type", "dr/cr", "cr/dr", "d/c", "txn type", "transaction type"
    ],
    "balance": [
        "balance", "closing balance", "running balance", "avail balance", "bal"
    ],
}


def generate_transaction_fingerprint(
    tx_date: datetime,
    amount: Decimal,
    tx_type: str,
    description: str,
) -> str:
    """
    Generates a deterministic SHA-256 fingerprint for duplicate detection.
    """
    date_str = tx_date.strftime("%Y-%m-%d")
    norm_desc = re.sub(r"[^a-zA-Z0-9]", "", (description or "").lower())
    amt_str = f"{abs(amount):.2f}"
    raw_key = f"{date_str}|{amt_str}|{tx_type.lower()}|{norm_desc}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def detect_column_mapping(headers: List[str]) -> Dict[str, str]:
    """
    Auto-detects semantic column roles from statement headers.
    """
    mapping: Dict[str, str] = {}
    normalized_headers = [(h, re.sub(r"[^a-z0-9]", " ", str(h).lower()).strip()) for h in headers]

    for role, aliases in COLUMN_ALIASES.items():
        for orig, norm in normalized_headers:
            if orig in mapping.values():
                continue
            for alias in aliases:
                if norm == alias or alias in norm:
                    mapping[role] = orig
                    break
            if role in mapping:
                break

    return mapping


def parse_date_string(date_str: Any) -> Optional[datetime]:
    if isinstance(date_str, datetime):
        return date_str

    s = str(date_str).strip()
    if not s:
        return None

    # Common bank statement date formats
    date_formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
        "%d-%b-%Y", "%d-%B-%Y", "%d %b %Y", "%d %B %Y",
        "%d-%b-%y", "%d/%m/%y", "%m/%d/%y", "%Y/%m/%d",
        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass

    return None


def parse_amount_value(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    if isinstance(val, (int, float, Decimal)):
        num = Decimal(str(val))
        return abs(num) if num != 0 else Decimal("0.00")

    s = str(val).strip().replace(",", "").replace("$", "").replace("₹", "").replace("Rs", "").replace("rs", "")
    s = re.sub(r"[^\d.-]", "", s)
    if not s or s == "-":
        return None

    try:
        amt = Decimal(s)
        return abs(amt)
    except InvalidOperation:
        return None


def parse_csv_content(
    file_bytes: bytes,
    custom_mapping: Optional[Dict[str, str]] = None,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    # Try decoding utf-8, fallback to latin-1
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")

    # Detect delimiter
    sample = text[:2048]
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample, delimiters=",\t;|")
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ","

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)

    if not rows:
        return [], []

    # Find the header row (row containing date/description/amount keywords)
    header_idx = 0
    for idx, row in enumerate(rows[:10]):
        row_str = " ".join(str(c).lower() for c in row)
        if any(k in row_str for k in ["date", "particular", "narration", "debit", "credit", "amount"]):
            header_idx = idx
            break

    headers = [str(c).strip() for c in rows[header_idx] if str(c).strip()]
    data_rows = []
    for r in rows[header_idx + 1:]:
        if any(cell.strip() for cell in r):
            row_dict = {headers[i]: r[i] for i in range(min(len(headers), len(r)))}
            data_rows.append(row_dict)

    return headers, data_rows


def parse_xlsx_content(
    file_bytes: bytes,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    sheet = wb.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return [], []

    # Find header row
    header_idx = 0
    for idx, row in enumerate(rows[:15]):
        row_str = " ".join(str(c).lower() for c in row if c is not None)
        if any(k in row_str for k in ["date", "particular", "narration", "debit", "credit", "amount"]):
            header_idx = idx
            break

    headers = [str(c).strip() for c in rows[header_idx] if c is not None]
    data_rows = []
    for r in rows[header_idx + 1:]:
        if any(cell is not None for cell in r):
            row_dict = {headers[i]: r[i] for i in range(min(len(headers), len(r)))}
            data_rows.append(row_dict)

    return headers, data_rows


def parse_pdf_content(
    file_bytes: bytes,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Extracts text-based tables from PDF statements.
    """
    reader = PdfReader(io.BytesIO(file_bytes))
    full_text = ""
    for page in reader.pages:
        txt = page.extract_text() or ""
        full_text += txt + "\n"

    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    headers = ["Date", "Description", "Debit", "Credit", "Balance"]
    data_rows: List[Dict[str, Any]] = []

    # Regular expression to match standard statement line: date, description, amounts
    line_pattern = re.compile(
        r"(\d{2}[-/.]\d{2}[-/.]\d{2,4}|\d{4}[-/.]\d{2}[-/.]\d{2})\s+(.+?)\s+([0-9,]+\.[0-9]{2})(?:\s+([0-9,]+\.[0-9]{2}))?"
    )

    for line in lines:
        m = line_pattern.search(line)
        if m:
            d_str = m.group(1)
            desc_str = m.group(2).strip()
            amt1 = m.group(3)
            amt2 = m.group(4)

            # Assign to debit/credit
            row_dict = {
                "Date": d_str,
                "Description": desc_str,
                "Debit": amt1 if amt2 else amt1,
                "Credit": amt2 if amt2 else "",
                "Balance": "",
            }
            data_rows.append(row_dict)

    return headers, data_rows


def process_statement_file(
    file_bytes: bytes,
    filename: str,
    existing_fingerprints: Optional[Set[str]] = None,
    custom_mapping: Optional[Dict[str, str]] = None,
) -> StatementImportPreviewResult:
    """
    Unified statement processing pipeline:
    Validates file -> Extracts columns -> Maps headers -> Normalizes rows ->
    Categorizes -> Classifies Essentiality -> Detects Duplicates -> Returns Preview.
    """
    if existing_fingerprints is None:
        existing_fingerprints = set()

    fn = filename.lower()
    file_type = "csv"
    if fn.endswith(".xlsx") or fn.endswith(".xls"):
        file_type = "xlsx"
        headers, raw_rows = parse_xlsx_content(file_bytes)
    elif fn.endswith(".pdf"):
        file_type = "pdf"
        headers, raw_rows = parse_pdf_content(file_bytes)
    else:
        file_type = "csv"
        headers, raw_rows = parse_csv_content(file_bytes)

    if not headers or not raw_rows:
        return StatementImportPreviewResult(
            filename=filename,
            file_type=file_type,
            total_rows=0,
            valid_count=0,
            duplicate_count=0,
            skipped_count=0,
            detected_columns={},
            transactions=[],
            errors=["No transaction records or headers found in statement file."],
        )

    # Detect column mapping
    mapping = custom_mapping or detect_column_mapping(headers)

    date_col = mapping.get("date")
    desc_col = mapping.get("description")
    amt_col = mapping.get("amount")
    debit_col = mapping.get("debit")
    credit_col = mapping.get("credit")
    type_col = mapping.get("type")

    normalized_txs: List[NormalizedStatementTransaction] = []
    seen_fingerprints: Set[str] = set(existing_fingerprints)
    valid_count = 0
    dup_count = 0
    skipped_count = 0

    for idx, row in enumerate(raw_rows):
        row_num = idx + 1

        # 1. Extract and validate Date
        raw_date = row.get(date_col) if date_col else None
        tx_date = parse_date_string(raw_date) if raw_date is not None else None

        if not tx_date:
            skipped_count += 1
            normalized_txs.append(
                NormalizedStatementTransaction(
                    row_index=row_num,
                    transaction_date=datetime.now(),
                    amount=Decimal("0.00"),
                    type="expense",
                    category="Miscellaneous",
                    description=str(row.get(desc_col, "Malformed row")),
                    essentiality="discretionary",
                    essentiality_reason="Invalid date row skipped",
                    fingerprint="",
                    is_valid=False,
                    error_message=f"Missing or invalid date format: '{raw_date}'",
                )
            )
            continue

        # 2. Extract Amount & Type
        tx_type = "expense"
        amount: Optional[Decimal] = None

        if debit_col and credit_col:
            debit_val = parse_amount_value(row.get(debit_col))
            credit_val = parse_amount_value(row.get(credit_col))

            if debit_val and debit_val > 0:
                amount = debit_val
                tx_type = "expense"
            elif credit_val and credit_val > 0:
                amount = credit_val
                tx_type = "income"
        elif amt_col:
            amt_raw = row.get(amt_col)
            amount = parse_amount_value(amt_raw)

            # Check if amount was negative
            if str(amt_raw).strip().startswith("-"):
                tx_type = "expense"
            elif type_col and row.get(type_col):
                t_str = str(row.get(type_col)).strip().lower()
                if "cr" in t_str or "credit" in t_str or "income" in t_str:
                    tx_type = "income"
                else:
                    tx_type = "expense"

        if not amount or amount <= 0:
            skipped_count += 1
            normalized_txs.append(
                NormalizedStatementTransaction(
                    row_index=row_num,
                    transaction_date=tx_date,
                    amount=Decimal("0.00"),
                    type="expense",
                    category="Miscellaneous",
                    description=str(row.get(desc_col, "Zero amount row")),
                    essentiality="discretionary",
                    essentiality_reason="Zero or non-numeric amount row",
                    fingerprint="",
                    is_valid=False,
                    error_message="Zero or missing amount value.",
                )
            )
            continue

        # 3. Description & Categorization
        raw_desc = str(row.get(desc_col, "")).strip() if desc_col else ""
        if not raw_desc:
            raw_desc = f"{tx_type.capitalize()} on {tx_date.strftime('%Y-%m-%d')}"

        cat_res = categorize_transaction(description=raw_desc, tx_type=tx_type)
        ess_res = classify_essentiality(category=cat_res.category, description=raw_desc, tx_type=tx_type)

        # 4. Fingerprint & Duplicate check
        fp = generate_transaction_fingerprint(
            tx_date=tx_date,
            amount=amount,
            tx_type=tx_type,
            description=raw_desc,
        )

        is_dup = fp in seen_fingerprints
        if is_dup:
            dup_count += 1
        else:
            seen_fingerprints.add(fp)
            valid_count += 1

        normalized_txs.append(
            NormalizedStatementTransaction(
                row_index=row_num,
                transaction_date=tx_date,
                amount=amount,
                type=tx_type,
                category=cat_res.category,
                description=raw_desc,
                essentiality=ess_res.essentiality,
                essentiality_reason=ess_res.reason,
                fingerprint=fp,
                is_duplicate=is_dup,
                is_valid=True,
            )
        )

    return StatementImportPreviewResult(
        filename=filename,
        file_type=file_type,
        total_rows=len(raw_rows),
        valid_count=valid_count,
        duplicate_count=dup_count,
        skipped_count=skipped_count,
        detected_columns=mapping,
        transactions=normalized_txs,
    )
