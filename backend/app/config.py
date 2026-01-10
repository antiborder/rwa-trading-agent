"""設定管理"""
import os
from typing import List

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
DYNAMODB_TABLE_PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "rwa_trading_agent")

# DynamoDB テーブル名
JUDGMENTS_TABLE = f"{DYNAMODB_TABLE_PREFIX}_judgments"
TRANSACTIONS_TABLE = f"{DYNAMODB_TABLE_PREFIX}_transactions"
PORTFOLIO_SNAPSHOTS_TABLE = f"{DYNAMODB_TABLE_PREFIX}_portfolio_snapshots"
PRICE_HISTORY_TABLE = f"{DYNAMODB_TABLE_PREFIX}_price_history"

# CORS設定
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

