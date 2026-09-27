from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy.orm import Session

from app.financial_engine.statement_importer import (
    StatementImportPreviewResult,
    generate_transaction_fingerprint,
    process_statement_file,
)
from app.models.transaction import Transaction
from app.schemas.transaction import (
    StatementImportConfirmItem,
    StatementImportConfirmResponse,
    StatementImportPreviewResponse,
    StatementRowPreview,
    TransactionResponse,
)


def get_user_transaction_fingerprints(
    db: Session,
    user_id: UUID,
) -> Set[str]:
    """
    Computes fingerprints for all existing transactions of a user to avoid duplicate imports.
    """
    txs = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    fingerprints = set()
    for t in txs:
        fp = generate_transaction_fingerprint(
            tx_date=t.transaction_date,
            amount=t.amount,
            tx_type=t.type,
            description=t.description or "",
        )
        fingerprints.add(fp)
    return fingerprints


def preview_statement_import(
    db: Session,
    user_id: UUID,
    file_bytes: bytes,
    filename: str,
    custom_mapping: Optional[Dict[str, str]] = None,
) -> StatementImportPreviewResponse:
    existing_fps = get_user_transaction_fingerprints(db, user_id)
    preview_res: StatementImportPreviewResult = process_statement_file(
        file_bytes=file_bytes,
        filename=filename,
        existing_fingerprints=existing_fps,
        custom_mapping=custom_mapping,
    )

    row_previews = [
        StatementRowPreview(
            row_index=t.row_index,
            transaction_date=t.transaction_date,
            amount=t.amount,
            type=t.type,  # type: ignore
            category=t.category,
            description=t.description,
            essentiality=t.essentiality,  # type: ignore
            essentiality_reason=t.essentiality_reason,
            fingerprint=t.fingerprint,
            is_duplicate=t.is_duplicate,
            is_valid=t.is_valid,
            error_message=t.error_message,
        )
        for t in preview_res.transactions
    ]

    return StatementImportPreviewResponse(
        filename=preview_res.filename,
        file_type=preview_res.file_type,
        total_rows=preview_res.total_rows,
        valid_count=preview_res.valid_count,
        duplicate_count=preview_res.duplicate_count,
        skipped_count=preview_res.skipped_count,
        detected_columns=preview_res.detected_columns,
        transactions=row_previews,
        errors=preview_res.errors,
    )


def confirm_statement_import(
    db: Session,
    user_id: UUID,
    transactions_to_import: List[StatementImportConfirmItem],
) -> StatementImportConfirmResponse:
    existing_fps = get_user_transaction_fingerprints(db, user_id)
    created_txs: List[Transaction] = []
    skipped_dups = 0

    for item in transactions_to_import:
        fp = item.fingerprint or generate_transaction_fingerprint(
            tx_date=item.transaction_date,
            amount=item.amount,
            tx_type=item.type,
            description=item.description or "",
        )

        if fp in existing_fps:
            skipped_dups += 1
            continue

        existing_fps.add(fp)

        tx = Transaction(
            user_id=user_id,
            amount=item.amount,
            type=item.type.lower(),
            category=item.category.strip(),
            description=item.description.strip() if item.description else None,
            transaction_date=item.transaction_date,
        )
        db.add(tx)
        created_txs.append(tx)

    db.commit()

    for tx in created_txs:
        db.refresh(tx)

    tx_responses = [TransactionResponse.model_validate(t) for t in created_txs]

    return StatementImportConfirmResponse(
        imported_count=len(tx_responses),
        skipped_duplicates_count=skipped_dups,
        transactions=tx_responses,
    )
