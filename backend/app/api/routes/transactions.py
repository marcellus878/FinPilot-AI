from datetime import datetime
import json
from typing import List, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.transaction import (
    HiddenExpenseResponse,
    MiscellaneousSpendingResponse,
    NLParseRequest,
    NLParseResponse,
    RecurringExpenseResponse,
    SpendingHabitResponse,
    SpendingIntelligenceResponse,
    SpendingPatternResponse,
    StatementImportConfirmRequest,
    StatementImportConfirmResponse,
    StatementImportPreviewResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.statement_service import (
    confirm_statement_import,
    preview_statement_import,
)
from app.services.transaction_service import (
    create_transaction,
    delete_transaction,
    get_transaction,
    get_user_spending_intelligence,
    list_transactions,
    parse_transaction_text,
    update_transaction,
)

router = APIRouter()


# ---------------- Natural Language & Voice Parsing ----------------

@router.post("/parse-text", response_model=NLParseResponse, status_code=status.HTTP_200_OK)
def parse_text_transaction(
    payload: NLParseRequest,
    current_user: User = Depends(get_current_user),
) -> NLParseResponse:
    return parse_transaction_text(
        text=payload.text,
        reference_date=payload.reference_date,
    )


# ---------------- Statement Ingestion Pipeline ----------------

@router.post("/import/preview", response_model=StatementImportPreviewResponse, status_code=status.HTTP_200_OK)
async def preview_statement_upload(
    file: UploadFile = File(..., description="Statement file in CSV, XLSX, or PDF format"),
    custom_mapping: Optional[str] = Form(None, description="Optional JSON string of column mapping overrides"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StatementImportPreviewResponse:
    mapping_dict = None
    if custom_mapping:
        try:
            mapping_dict = json.loads(custom_mapping)
        except Exception:
            pass

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    return preview_statement_import(
        db=db,
        user_id=current_user.id,
        file_bytes=file_bytes,
        filename=file.filename or "statement.csv",
        custom_mapping=mapping_dict,
    )


@router.post("/import/confirm", response_model=StatementImportConfirmResponse, status_code=status.HTTP_201_CREATED)
def confirm_statement_upload(
    payload: StatementImportConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StatementImportConfirmResponse:
    return confirm_statement_import(
        db=db,
        user_id=current_user.id,
        transactions_to_import=payload.transactions,
    )


# ---------------- Spending Intelligence & Analytics ----------------

@router.get("/intelligence", response_model=SpendingIntelligenceResponse, status_code=status.HTTP_200_OK)
def get_spending_intelligence(
    start_date: Optional[datetime] = Query(None, description="Start date of analysis window"),
    end_date: Optional[datetime] = Query(None, description="End date of analysis window"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SpendingIntelligenceResponse:
    return get_user_spending_intelligence(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/patterns", response_model=List[SpendingPatternResponse], status_code=status.HTTP_200_OK)
def get_spending_patterns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[SpendingPatternResponse]:
    intel = get_user_spending_intelligence(db=db, user_id=current_user.id)
    return intel.patterns


@router.get("/recurring", response_model=List[RecurringExpenseResponse], status_code=status.HTTP_200_OK)
def get_recurring_expenses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[RecurringExpenseResponse]:
    intel = get_user_spending_intelligence(db=db, user_id=current_user.id)
    return intel.recurring_expenses


@router.get("/hidden-expenses", response_model=List[HiddenExpenseResponse], status_code=status.HTTP_200_OK)
def get_hidden_expenses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[HiddenExpenseResponse]:
    intel = get_user_spending_intelligence(db=db, user_id=current_user.id)
    return intel.hidden_expenses


@router.get("/miscellaneous", response_model=MiscellaneousSpendingResponse, status_code=status.HTTP_200_OK)
def get_miscellaneous_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MiscellaneousSpendingResponse:
    intel = get_user_spending_intelligence(db=db, user_id=current_user.id)
    return intel.miscellaneous_analysis


# ---------------- Core Transaction CRUD ----------------

@router.get("", response_model=List[TransactionResponse], status_code=status.HTTP_200_OK)
def get_transactions(
    start_date: Optional[datetime] = Query(None, description="Filter transactions after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter transactions before this date"),
    category: Optional[str] = Query(None, description="Filter by category substring"),
    type: Optional[str] = Query(None, description="Filter by transaction type: income or expense"),
    limit: int = Query(200, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[TransactionResponse]:
    return list_transactions(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        category=category,
        tx_type=type,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_new_transaction(
    tx_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionResponse:
    return create_transaction(db=db, user_id=current_user.id, tx_in=tx_in)


@router.get("/{transaction_id}", response_model=TransactionResponse, status_code=status.HTTP_200_OK)
def get_transaction_by_id(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionResponse:
    tx = get_transaction(db=db, user_id=current_user.id, transaction_id=transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return tx


@router.put("/{transaction_id}", response_model=TransactionResponse, status_code=status.HTTP_200_OK)
def update_existing_transaction(
    transaction_id: UUID,
    tx_in: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionResponse:
    tx = update_transaction(db=db, user_id=current_user.id, transaction_id=transaction_id, tx_in=tx_in)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return tx


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = delete_transaction(db=db, user_id=current_user.id, transaction_id=transaction_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return None
