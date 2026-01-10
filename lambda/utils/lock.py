"""実行ロック管理"""
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from config import EXECUTION_LOCKS_TABLE, AWS_REGION
from utils.logger import logger

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
lock_table = dynamodb.Table(EXECUTION_LOCKS_TABLE)


def acquire_lock() -> bool:
    """実行ロックを取得"""
    try:
        expires_at = int((datetime.utcnow() + timedelta(minutes=10)).timestamp())
        lock_table.put_item(
            Item={
                'lock_id': 'main_execution',
                'locked_at': datetime.utcnow().isoformat(),
                'expires_at': expires_at
            },
            ConditionExpression='attribute_not_exists(lock_id)'
        )
        logger.info("Lock acquired successfully")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.warning("Lock already exists, skipping execution")
            return False  # 既にロックされている
        logger.error(f"Failed to acquire lock: {str(e)}")
        raise


def release_lock():
    """実行ロックを解放"""
    try:
        lock_table.delete_item(Key={'lock_id': 'main_execution'})
        logger.info("Lock released successfully")
    except Exception as e:
        logger.error(f"Failed to release lock: {str(e)}")

