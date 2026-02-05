"""DynamoDBサービス"""
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from app.config import (
    JUDGMENTS_TABLE, TRANSACTIONS_TABLE, PORTFOLIO_SNAPSHOTS_TABLE,
    PRICE_HISTORY_TABLE, AWS_REGION
)


class DynamoDBService:
    """DynamoDBサービス"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        self.judgments_table = self.dynamodb.Table(JUDGMENTS_TABLE)
        self.transactions_table = self.dynamodb.Table(TRANSACTIONS_TABLE)
        self.portfolio_snapshots_table = self.dynamodb.Table(PORTFOLIO_SNAPSHOTS_TABLE)
        self.price_history_table = self.dynamodb.Table(PRICE_HISTORY_TABLE)
    
    def _decimal_to_float(self, value):
        """Decimalをfloatに変換"""
        if isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, dict):
            return {k: self._decimal_to_float(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._decimal_to_float(item) for item in value]
        return value
    
    def get_latest_portfolio_snapshot(self) -> Optional[Dict]:
        """最新のポートフォリオスナップショットを取得"""
        try:
            response = self.portfolio_snapshots_table.scan(
                Limit=1
            )
            
            if response['Items']:
                # 最新のものを取得（timestampでソート）
                items = sorted(
                    response['Items'],
                    key=lambda x: x['timestamp'],
                    reverse=True
                )
                item = items[0]
                return self._decimal_to_float(item)
            return None
        except Exception as e:
            print(f"Error getting portfolio snapshot: {str(e)}")
            return None
    
    def get_portfolio_performance(self, days: int) -> Optional[Dict]:
        """指定日数前のポートフォリオスナップショットを取得"""
        try:
            target_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            response = self.portfolio_snapshots_table.scan()
            items = response['Items']
            
            # 指定日数前の最も近いスナップショットを取得
            closest_item = None
            closest_diff = None
            
            for item in items:
                item_date = item['timestamp']
                if item_date <= target_date:
                    diff = (datetime.fromisoformat(target_date) - 
                           datetime.fromisoformat(item_date)).total_seconds()
                    if closest_diff is None or diff < closest_diff:
                        closest_item = item
                        closest_diff = diff
            
            if closest_item:
                return self._decimal_to_float(closest_item)
            return None
        except Exception as e:
            print(f"Error getting portfolio performance: {str(e)}")
            return None
    
    def get_judgments(self, limit: int = 50, last_key: Optional[str] = None) -> Dict:
        """判断履歴一覧を取得"""
        try:
            # 最新取得はGSIでQuery（record_type固定 + timestamp降順 + Limit）
            # NOTE: 既存データ（record_type未付与）が残っている間はフォールバックでscanも実施。
            if last_key:
                # このプロジェクトのlast_keyはフロントで未使用。互換のためscanベースのページングは温存しない。
                pass

            try:
                response = self.judgments_table.query(
                    IndexName="judgments_by_record_type_timestamp",
                    KeyConditionExpression=Key("record_type").eq("judgment"),
                    ScanIndexForward=False,
                    Limit=limit,
                )
                items = response.get("Items", [])
            except Exception:
                items = []

            if len(items) < limit:
                # フォールバック: scanしてtimestamp降順から補完（テーブルが小さい間の暫定）
                scan_items: List[Dict] = []
                scan_kwargs: Dict = {}
                while True:
                    scan_resp = self.judgments_table.scan(**scan_kwargs)
                    scan_items.extend(scan_resp.get("Items", []))
                    lek = scan_resp.get("LastEvaluatedKey")
                    if not lek:
                        break
                    scan_kwargs["ExclusiveStartKey"] = lek

                scan_items_sorted = sorted(scan_items, key=lambda x: x["timestamp"], reverse=True)
                items = scan_items_sorted[:limit]

            return {
                "items": [self._decimal_to_float(item) for item in items],
                "last_evaluated_key": None,
            }
        except Exception as e:
            print(f"Error getting judgments: {str(e)}")
            return {'items': [], 'last_evaluated_key': None}
    
    def get_judgment(self, judgment_id: str) -> Optional[Dict]:
        """特定の判断履歴を取得"""
        try:
            # judgment_idとtimestampの両方が必要なので、スキャンで検索
            response = self.judgments_table.scan(
                FilterExpression='judgment_id = :id',
                ExpressionAttributeValues={':id': judgment_id}
            )
            
            if response['Items']:
                return self._decimal_to_float(response['Items'][0])
            return None
        except Exception as e:
            print(f"Error getting judgment: {str(e)}")
            return None
    
    def get_transactions(self, limit: int = 50, last_key: Optional[str] = None) -> Dict:
        """取引履歴一覧を取得"""
        try:
            scan_kwargs = {
                'Limit': limit
            }
            
            if last_key:
                scan_kwargs['ExclusiveStartKey'] = {'transaction_id': last_key}
            
            response = self.transactions_table.scan(**scan_kwargs)
            
            items = sorted(
                response['Items'],
                key=lambda x: x['timestamp'],
                reverse=True
            )
            
            return {
                'items': [self._decimal_to_float(item) for item in items],
                'last_evaluated_key': response.get('LastEvaluatedKey')
            }
        except Exception as e:
            print(f"Error getting transactions: {str(e)}")
            return {'items': [], 'last_evaluated_key': None}
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict]:
        """特定の取引履歴を取得"""
        try:
            response = self.transactions_table.scan(
                FilterExpression='transaction_id = :id',
                ExpressionAttributeValues={':id': transaction_id}
            )
            
            if response['Items']:
                return self._decimal_to_float(response['Items'][0])
            return None
        except Exception as e:
            print(f"Error getting transaction: {str(e)}")
            return None
    
    def get_price_history(self, symbol: str, days: int = 30) -> List[Dict]:
        """価格履歴を取得"""
        try:
            response = self.price_history_table.query(
                KeyConditionExpression='symbol = :symbol',
                ExpressionAttributeValues={':symbol': symbol},
                ScanIndexForward=False,
                Limit=days
            )
            
            return [self._decimal_to_float(item) for item in response['Items']]
        except Exception as e:
            print(f"Error getting price history: {str(e)}")
            return []

