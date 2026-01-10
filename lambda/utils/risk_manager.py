"""リスク管理"""
from typing import Dict, Tuple
from config import (
    MAX_SPREAD_PERCENT, BALANCE_USAGE_RATIO, MAX_PRICE_DEVIATION_PERCENT
)
from utils.logger import logger
from utils.gateio_client import GateIOClient


class RiskManager:
    """リスク管理"""
    
    def __init__(self, gateio_client: GateIOClient):
        self.gateio_client = gateio_client
    
    def check_spread(self, symbol: str) -> bool:
        """スプレッドチェック"""
        orderbook = self.gateio_client.get_order_book(symbol)
        if orderbook and orderbook.get('spread_percent'):
            spread = orderbook['spread_percent']
            if spread > MAX_SPREAD_PERCENT:
                logger.warning(f"Spread too high for {symbol}: {spread:.2f}%")
                return False
        return True
    
    def calculate_order_amount(self, balance: float, target_ratio: float) -> float:
        """注文数量を計算（手数料を考慮）"""
        return balance * target_ratio * BALANCE_USAGE_RATIO
    
    def check_price_deviation(self, symbol: str, current_price: float) -> bool:
        """価格乖離チェック（週末のデペグ防止）"""
        # TODO: 直近終値と比較する実装が必要
        # ここでは簡易実装
        # 実際にはprice_historyテーブルから直近の価格を取得して比較
        return True  # 暫定的にTrueを返す
    
    def validate_trade(self, symbol: str, side: str, amount: float) -> Tuple[bool, str]:
        """取引の妥当性を検証"""
        # スプレッドチェック
        if not self.check_spread(symbol):
            return False, f"Spread too high for {symbol}"
        
        # 価格乖離チェック
        ticker = self.gateio_client.get_ticker(symbol)
        if not self.check_price_deviation(symbol, ticker['price']):
            return False, f"Price deviation too high for {symbol}"
        
        # 最小注文数量チェック（Gate.ioの仕様に応じて調整）
        if amount < 0.001:  # 最小注文数量の例
            return False, f"Order amount too small: {amount}"
        
        return True, "OK"

