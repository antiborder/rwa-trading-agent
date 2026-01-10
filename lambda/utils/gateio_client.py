"""Gate.io API クライアント"""
import ccxt
from typing import Dict, List, Optional
from config import GATEIO_API_KEY, GATEIO_API_SECRET, TRADING_SYMBOLS
from utils.logger import logger


class GateIOClient:
    """Gate.io API クライアント"""
    
    def __init__(self):
        self.exchange = ccxt.gateio({
            'apiKey': GATEIO_API_KEY,
            'secret': GATEIO_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',  # spot, future, delivery
            }
        })
    
    def get_balance(self) -> Dict[str, float]:
        """残高を取得"""
        try:
            balance = self.exchange.fetch_balance()
            return balance['total']  # 利用可能残高 + 注文中残高
        except Exception as e:
            logger.error(f"Failed to fetch balance: {str(e)}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict:
        """ティッカー情報を取得"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                "symbol": symbol,
                "price": ticker['last'],
                "change_24h": ticker['percentage'],
                "volume": ticker['quoteVolume']
            }
        except Exception as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {str(e)}")
            raise
    
    def get_all_tickers(self) -> Dict[str, Dict]:
        """全シンボルのティッカー情報を取得"""
        tickers = {}
        for symbol in TRADING_SYMBOLS:
            try:
                tickers[symbol] = self.get_ticker(symbol)
            except Exception as e:
                logger.warning(f"Failed to fetch ticker for {symbol}: {str(e)}")
        return tickers
    
    def get_order_book(self, symbol: str, limit: int = 5) -> Dict:
        """オーダーブックを取得"""
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit)
            bid_price = orderbook['bids'][0][0] if orderbook['bids'] else None
            ask_price = orderbook['asks'][0][0] if orderbook['asks'] else None
            
            if bid_price and ask_price:
                spread = ((ask_price - bid_price) / bid_price) * 100
                return {
                    "symbol": symbol,
                    "bid_price": bid_price,
                    "ask_price": ask_price,
                    "spread_percent": spread
                }
            return None
        except Exception as e:
            logger.error(f"Failed to fetch order book for {symbol}: {str(e)}")
            return None
    
    def create_market_order(self, symbol: str, side: str, amount: float) -> Optional[Dict]:
        """成行注文を発注"""
        try:
            order = self.exchange.create_market_order(symbol, side, amount)
            return {
                "order_id": order['id'],
                "symbol": symbol,
                "side": side,
                "amount": order['amount'],
                "price": order.get('price'),
                "status": order['status']
            }
        except Exception as e:
            logger.error(f"Failed to create market order: {str(e)}")
            return None

