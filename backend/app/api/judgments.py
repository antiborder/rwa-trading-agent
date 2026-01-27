"""判断履歴API"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.models.schemas import JudgmentResponse
from app.services.dynamodb_service import DynamoDBService

router = APIRouter(prefix="/api/judgments", tags=["judgments"])
db_service = DynamoDBService()


@router.get("", response_model=List[JudgmentResponse])
async def get_judgments(
    limit: int = Query(50, ge=1, le=100),
    last_key: Optional[str] = Query(None)
):
    """判断履歴一覧を取得"""
    result = db_service.get_judgments(limit=limit, last_key=last_key)
    return [JudgmentResponse(**item) for item in result['items']]


@router.get("/{judgment_id}", response_model=JudgmentResponse)
async def get_judgment(judgment_id: str):
    """特定の判断履歴を取得"""
    judgment = db_service.get_judgment(judgment_id)
    
    if not judgment:
        raise HTTPException(status_code=404, detail="Judgment not found")
    
    return JudgmentResponse(**judgment)

