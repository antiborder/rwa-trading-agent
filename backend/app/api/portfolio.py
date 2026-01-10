"""ポートフォリオAPI"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import datetime
from app.models.schemas import (
    PortfolioCurrentResponse, PerformanceResponse, CurrencyPerformanceResponse
)
from app.services.dynamodb_service import DynamoDBService

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])
db_service = DynamoDBService()


@router.get("/current", response_model=PortfolioCurrentResponse)
async def get_current_portfolio():
    """現在の資産内訳を取得"""
    snapshot = db_service.get_latest_portfolio_snapshot()
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Portfolio snapshot not found")
    
    return PortfolioCurrentResponse(
        holdings=snapshot['holdings'],
        values_usdt=snapshot['values_usdt'],
        total_value_usdt=snapshot['total_value_usdt'],
        allocations=snapshot['allocations'],
        timestamp=snapshot['timestamp']
    )


@router.get("/performance", response_model=List[PerformanceResponse])
async def get_portfolio_performance():
    """資産全体の騰落率を取得（1日/2日/1週間/2週間/1ヶ月）"""
    periods = [1, 2, 7, 14, 30]
    current_snapshot = db_service.get_latest_portfolio_snapshot()
    
    if not current_snapshot:
        raise HTTPException(status_code=404, detail="Current portfolio snapshot not found")
    
    current_value = current_snapshot['total_value_usdt']
    performances = []
    
    for days in periods:
        past_snapshot = db_service.get_portfolio_performance(days)
        
        if past_snapshot:
            past_value = past_snapshot['total_value_usdt']
            change_percent = ((current_value - past_value) / past_value) * 100 if past_value > 0 else 0
        else:
            change_percent = 0.0
        
        period_name = f"{days}日" if days < 7 else f"{days//7}週間" if days < 30 else "1ヶ月"
        
        performances.append(PerformanceResponse(
            period=period_name,
            total_value_usdt=current_value,
            change_percent=change_percent
        ))
    
    return performances


@router.get("/currency-performance", response_model=List[CurrencyPerformanceResponse])
async def get_currency_performance():
    """各通貨の騰落率を取得"""
    # 最新の価格履歴から各通貨の騰落率を計算
    symbols = [
        "PAXG/USDT", "KAG/USDT", "SPYON/USDT", "QQQON/USDT",
        "TSLAX/USDT", "NVDAX/USDT", "MSTRX/USDT",
        "EURS/USDT", "GBPT/USDT", "ONDO/USDT"
    ]
    
    performances = []
    
    for symbol in symbols:
        price_history = db_service.get_price_history(symbol, days=30)
        
        if price_history:
            latest = price_history[0]
            current_price = latest['price']
            change_24h = latest['change_24h']
            
            # 1日/1週間/1ヶ月前の価格を取得
            change_1d = None
            change_1w = None
            change_1m = None
            
            for price_data in price_history:
                days_ago = (datetime.fromisoformat(latest['timestamp']) - 
                           datetime.fromisoformat(price_data['timestamp'])).days
                
                if days_ago >= 1 and change_1d is None:
                    change_1d = ((current_price - price_data['price']) / price_data['price']) * 100
                if days_ago >= 7 and change_1w is None:
                    change_1w = ((current_price - price_data['price']) / price_data['price']) * 100
                if days_ago >= 30 and change_1m is None:
                    change_1m = ((current_price - price_data['price']) / price_data['price']) * 100
                    break
            
            performances.append(CurrencyPerformanceResponse(
                symbol=symbol,
                current_price=current_price,
                change_24h=change_24h,
                change_1d=change_1d,
                change_1w=change_1w,
                change_1m=change_1m
            ))
    
    return performances

