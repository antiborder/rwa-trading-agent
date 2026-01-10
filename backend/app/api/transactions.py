"""取引履歴API"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.models.schemas import TransactionResponse
from app.services.dynamodb_service import DynamoDBService

router = APIRouter(prefix="/api/transactions", tags=["transactions"])
db_service = DynamoDBService()


@router.get("", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = Query(50, ge=1, le=100),
    last_key: Optional[str] = Query(None)
):
    """取引履歴一覧を取得"""
    result = db_service.get_transactions(limit=limit, last_key=last_key)
    return [TransactionResponse(**item) for item in result['items']]


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str):
    """特定の取引履歴を取得"""
    transaction = db_service.get_transaction(transaction_id)
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return TransactionResponse(**transaction)

