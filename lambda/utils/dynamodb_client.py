"""DynamoDB クライアント"""
import boto3
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal
from config import (
    JUDGMENTS_TABLE, TRANSACTIONS_TABLE, PORTFOLIO_SNAPSHOTS_TABLE,
    PRICE_HISTORY_TABLE, AWS_REGION
)
from utils.logger import logger


class DynamoDBClient:
    """DynamoDB クライアント"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        self.judgments_table = self.dynamodb.Table(JUDGMENTS_TABLE)
        self.transactions_table = self.dynamodb.Table(TRANSACTIONS_TABLE)
        self.portfolio_snapshots_table = self.dynamodb.Table(PORTFOLIO_SNAPSHOTS_TABLE)
        self.price_history_table = self.dynamodb.Table(PRICE_HISTORY_TABLE)
    
    def save_judgment(self, confidence_score: int, reasoning: str, 
                     target_allocations: Dict[str, float],
                     source_urls: List[str], fetch_status: Dict[str, bool],
                     failed_sources: List[str]) -> str:
        """判断履歴を保存"""
        judgment_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'judgment_id': judgment_id,
            'timestamp': timestamp,
            'confidence_score': confidence_score,
            'target_allocations': {k: Decimal(str(v)) for k, v in target_allocations.items()},
            'reasoning_text': reasoning,
            'source_urls': source_urls,
            'info_fetch_status': {k: bool(v) for k, v in fetch_status.items()},
            'failed_sources': failed_sources
        }
        
        try:
            self.judgments_table.put_item(Item=item)
            logger.info(f"Judgment saved: {judgment_id}")
            return judgment_id
        except Exception as e:
            logger.error(f"Failed to save judgment: {str(e)}")
            raise
    
    def save_transaction(self, symbol: str, side: str, amount: float,
                        price: float, status: str,
                        pre_allocation: Dict[str, float],
                        post_allocation: Dict[str, float]) -> str:
        """取引履歴を保存"""
        transaction_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'transaction_id': transaction_id,
            'timestamp': timestamp,
            'symbol': symbol,
            'side': side,
            'amount': Decimal(str(amount)),
            'price': Decimal(str(price)),
            'status': status,
            'pre_allocation': {k: Decimal(str(v)) for k, v in pre_allocation.items()},
            'post_allocation': {k: Decimal(str(v)) for k, v in post_allocation.items()}
        }
        
        try:
            self.transactions_table.put_item(Item=item)
            logger.info(f"Transaction saved: {transaction_id}")
            return transaction_id
        except Exception as e:
            logger.error(f"Failed to save transaction: {str(e)}")
            raise
    
    def save_portfolio_snapshot(self, holdings: Dict[str, float],
                               values_usdt: Dict[str, float],
                               total_value_usdt: float,
                               allocations: Dict[str, float]) -> str:
        """資産スナップショットを保存"""
        snapshot_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'snapshot_id': snapshot_id,
            'timestamp': timestamp,
            'holdings': {k: Decimal(str(v)) for k, v in holdings.items()},
            'values_usdt': {k: Decimal(str(v)) for k, v in values_usdt.items()},
            'total_value_usdt': Decimal(str(total_value_usdt)),
            'allocations': {k: Decimal(str(v)) for k, v in allocations.items()}
        }
        
        try:
            self.portfolio_snapshots_table.put_item(Item=item)
            logger.info(f"Portfolio snapshot saved: {snapshot_id}")
            return snapshot_id
        except Exception as e:
            logger.error(f"Failed to save portfolio snapshot: {str(e)}")
            raise
    
    def save_price_history(self, symbol: str, price: float,
                          change_24h: float, volume: float):
        """価格履歴を保存"""
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'symbol': symbol,
            'timestamp': timestamp,
            'price': Decimal(str(price)),
            'change_24h': Decimal(str(change_24h)),
            'volume': Decimal(str(volume))
        }
        
        try:
            self.price_history_table.put_item(Item=item)
        except Exception as e:
            logger.error(f"Failed to save price history for {symbol}: {str(e)}")

