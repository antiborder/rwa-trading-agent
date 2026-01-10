"""DynamoDBテーブル作成スクリプト"""
import boto3
import os
from botocore.exceptions import ClientError

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
DYNAMODB_TABLE_PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "rwa_trading_agent")

dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)

tables = [
    {
        'TableName': f"{DYNAMODB_TABLE_PREFIX}_judgments",
        'KeySchema': [
            {'AttributeName': 'judgment_id', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'judgment_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST',
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'judgments_by_timestamp',
                'KeySchema': [
                    {'AttributeName': 'judgment_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    {
        'TableName': f"{DYNAMODB_TABLE_PREFIX}_transactions",
        'KeySchema': [
            {'AttributeName': 'transaction_id', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'transaction_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'},
            {'AttributeName': 'symbol', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST',
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'transactions_by_symbol',
                'KeySchema': [
                    {'AttributeName': 'symbol', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    {
        'TableName': f"{DYNAMODB_TABLE_PREFIX}_portfolio_snapshots",
        'KeySchema': [
            {'AttributeName': 'snapshot_id', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'snapshot_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST',
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'portfolio_snapshots_by_timestamp',
                'KeySchema': [
                    {'AttributeName': 'snapshot_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    {
        'TableName': f"{DYNAMODB_TABLE_PREFIX}_price_history",
        'KeySchema': [
            {'AttributeName': 'symbol', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'symbol', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    },
    {
        'TableName': f"{DYNAMODB_TABLE_PREFIX}_execution_locks",
        'KeySchema': [
            {'AttributeName': 'lock_id', 'KeyType': 'HASH'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'lock_id', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST',
        'TimeToLiveSpecification': {
            'Enabled': True,
            'AttributeName': 'expires_at'
        }
    }
]

def create_table(table_def):
    """テーブルを作成"""
    table_name = table_def['TableName']
    
    try:
        # 既存のテーブルをチェック
        dynamodb.describe_table(TableName=table_name)
        print(f"Table {table_name} already exists")
        return False
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # テーブルが存在しない場合は作成
            try:
                dynamodb.create_table(**table_def)
                print(f"Creating table {table_name}...")
                waiter = dynamodb.get_waiter('table_exists')
                waiter.wait(TableName=table_name)
                print(f"Table {table_name} created successfully")
                return True
            except Exception as create_error:
                print(f"Error creating table {table_name}: {str(create_error)}")
                return False
        else:
            print(f"Error checking table {table_name}: {str(e)}")
            return False

if __name__ == '__main__':
    print("Creating DynamoDB tables...")
    for table_def in tables:
        create_table(table_def)
    print("Done!")

