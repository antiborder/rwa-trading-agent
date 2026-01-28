"""設定管理"""
import os
from typing import List

# 取引対象資産
TRADING_SYMBOLS: List[str] = [
    "PAXG/USDT",  # Gold
    "SLVON/USDT", # Silver (iShares Silver Trust Ondo Tokenized)
    "SPYON/USDT", # S&P500
    "QQQON/USDT", # NASDAQ
    "TSLAX/USDT", # Tesla
    "NVDAX/USDT", # NVIDIA
    "MSTRX/USDT", # MicroStrategy
    "ONDO/USDT",  # US Treasury
]

# 環境変数
GATEIO_API_KEY = os.getenv("GATEIO_API_KEY")
GATEIO_API_SECRET = os.getenv("GATEIO_API_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
DYNAMODB_TABLE_PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "rwa_trading_agent")

# DynamoDB テーブル名
JUDGMENTS_TABLE = f"{DYNAMODB_TABLE_PREFIX}_judgments"
TRANSACTIONS_TABLE = f"{DYNAMODB_TABLE_PREFIX}_transactions"
PORTFOLIO_SNAPSHOTS_TABLE = f"{DYNAMODB_TABLE_PREFIX}_portfolio_snapshots"
PRICE_HISTORY_TABLE = f"{DYNAMODB_TABLE_PREFIX}_price_history"
EXECUTION_LOCKS_TABLE = f"{DYNAMODB_TABLE_PREFIX}_execution_locks"

# リスク管理設定
MAX_SPREAD_PERCENT = 0.5  # スプレッドが0.5%以上の場合はエントリーをスキップ
FEE_PERCENT = 0.2  # 手数料0.2%
BALANCE_USAGE_RATIO = 0.998  # 残高の99.8%で計算
MAX_PRICE_DEVIATION_PERCENT = 5.0  # 価格乖離5%以上でエントリー制限
MIN_CONFIDENCE_SCORE = 8  # Confidence Score 8以上でアクション検討

# ニュースソース
NEWS_SOURCES = {
    "reuters": "https://www.reuters.com/business/",
    "investing": "https://jp.investing.com/news/general",
    "cryptopanic": "https://cryptopanic.com/about/api/",
    "coindesk": "https://www.coindeskjapan.com/",
    "forexfactory": "https://www.forexfactory.com/calendar",
    "liveuamap": "https://liveuamap.com/",
}

