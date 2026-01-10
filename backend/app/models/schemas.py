"""Pydanticスキーマ"""
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class JudgmentResponse(BaseModel):
    """判断履歴レスポンス"""
    judgment_id: str
    timestamp: str
    confidence_score: int
    target_allocations: Dict[str, float]
    reasoning_text: str
    source_urls: List[str]
    info_fetch_status: Dict[str, bool]
    failed_sources: List[str]


class TransactionResponse(BaseModel):
    """取引履歴レスポンス"""
    transaction_id: str
    timestamp: str
    symbol: str
    side: str
    amount: float
    price: float
    status: str
    pre_allocation: Dict[str, float]
    post_allocation: Dict[str, float]


class PortfolioSnapshotResponse(BaseModel):
    """資産スナップショットレスポンス"""
    snapshot_id: str
    timestamp: str
    holdings: Dict[str, float]
    values_usdt: Dict[str, float]
    total_value_usdt: float
    allocations: Dict[str, float]


class PortfolioCurrentResponse(BaseModel):
    """現在の資産内訳レスポンス"""
    holdings: Dict[str, float]
    values_usdt: Dict[str, float]
    total_value_usdt: float
    allocations: Dict[str, float]
    timestamp: str


class PerformanceResponse(BaseModel):
    """騰落率レスポンス"""
    period: str
    total_value_usdt: float
    change_percent: float


class CurrencyPerformanceResponse(BaseModel):
    """通貨別騰落率レスポンス"""
    symbol: str
    current_price: float
    change_24h: float
    change_1d: Optional[float] = None
    change_1w: Optional[float] = None
    change_1m: Optional[float] = None

