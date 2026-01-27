"""メイン実行サイクル"""
import json
import os
from typing import Dict

# 環境変数の読み込み（ローカル開発環境のみ）
# Lambda環境では環境変数が直接設定されているため不要
# 注意: Lambda環境では dotenv を使用しない（環境変数が直接設定されている）
# ローカル開発時は、環境変数を直接設定するか、.envファイルを手動で読み込む

from config import MIN_CONFIDENCE_SCORE, TRADING_SYMBOLS
from utils.logger import logger
from utils.lock import acquire_lock, release_lock
from utils.news_collector import collect_news
from utils.gateio_client import GateIOClient
from utils.gemini_client import GeminiClient
from utils.dynamodb_client import DynamoDBClient
from utils.risk_manager import RiskManager


def calculate_current_allocations(balance: Dict[str, float], 
                                 tickers: Dict[str, Dict]) -> Dict[str, float]:
    """現在の資産配分を計算"""
    total_value = 0.0
    values = {}
    
    # 各資産のUSDT価値を計算
    for symbol in TRADING_SYMBOLS:
        if symbol in balance and balance[symbol] > 0:
            price = tickers.get(symbol, {}).get('price', 0)
            value = balance[symbol] * price
            values[symbol] = value
            total_value += value
    
    # USDT残高を追加
    if 'USDT' in balance:
        values['USDT'] = balance['USDT']
        total_value += balance['USDT']
    
    # 配分比率を計算
    if total_value > 0:
        allocations = {k: v / total_value for k, v in values.items()}
    else:
        allocations = {}
    
    return allocations


def calculate_trade_orders(current_allocations: Dict[str, float],
                          target_allocations: Dict[str, float],
                          total_value: float,
                          tickers: Dict[str, Dict]) -> list:
    """売買命令を計算"""
    orders = []
    
    for symbol in TRADING_SYMBOLS + ['USDT']:
        current_ratio = current_allocations.get(symbol, 0.0)
        target_ratio = target_allocations.get(symbol, 0.0)
        diff_ratio = target_ratio - current_ratio
        
        # 差分が0.01%未満の場合はスキップ
        if abs(diff_ratio) < 0.0001:
            continue
        
        if diff_ratio > 0:
            # 買い注文
            order_value = total_value * diff_ratio
            price = tickers.get(symbol, {}).get('price', 1.0) if symbol != 'USDT' else 1.0
            amount = order_value / price
            orders.append({
                'symbol': symbol,
                'side': 'buy',
                'amount': amount
            })
        else:
            # 売り注文
            order_value = total_value * abs(diff_ratio)
            price = tickers.get(symbol, {}).get('price', 1.0) if symbol != 'USDT' else 1.0
            amount = order_value / price
            orders.append({
                'symbol': symbol,
                'side': 'sell',
                'amount': amount
            })
    
    return orders


def lambda_handler(event, context):
    """
    メイン実行サイクル
    EventBridgeから5分間隔で呼び出される
    """
    # ロック取得
    if not acquire_lock():
        logger.info("Another execution is in progress, skipping")
        return {
            'statusCode': 200,
            'body': json.dumps('Skipped: Another execution in progress')
        }
    
    try:
        # クライアント初期化
        gateio_client = GateIOClient()
        gemini_client = GeminiClient()
        dynamodb_client = DynamoDBClient()
        risk_manager = RiskManager(gateio_client)
        
        # 1. 情報収集
        logger.info("Step 1: Collecting news")
        news_data = collect_news()
        
        # 2. 現在の残高と価格を取得
        logger.info("Step 2: Fetching balance and prices")
        balance = gateio_client.get_balance()
        tickers = gateio_client.get_all_tickers()
        
        # 価格履歴を保存
        for symbol, ticker_data in tickers.items():
            dynamodb_client.save_price_history(
                symbol,
                ticker_data['price'],
                ticker_data['change_24h'],
                ticker_data['volume']
            )
        
        # 現在の資産配分を計算
        current_allocations = calculate_current_allocations(balance, tickers)
        total_value = sum([
            balance.get(symbol, 0) * tickers.get(symbol, {}).get('price', 0)
            for symbol in TRADING_SYMBOLS
        ]) + balance.get('USDT', 0)
        
        # 3. 市場分析
        logger.info("Step 3: Analyzing market")
        price_data = {
            symbol: {
                'price': ticker['price'],
                'change_24h': ticker['change_24h']
            }
            for symbol, ticker in tickers.items()
        }
        
        confidence_score, reasoning = gemini_client.analyze_market(
            news_data['news_text'],
            price_data
        )
        
        logger.info(f"Confidence Score: {confidence_score}")
        
        # 4. ポートフォリオ最適化（Confidence Score 8以上の場合のみ）
        if confidence_score >= MIN_CONFIDENCE_SCORE:
            logger.info("Step 4: Optimizing portfolio")
            target_allocations = gemini_client.optimize_portfolio(
                reasoning,
                current_allocations
            )
            
            # 5. 売買命令を計算
            orders = calculate_trade_orders(
                current_allocations,
                target_allocations,
                total_value,
                tickers
            )
            
            # 6. リスク管理チェックと実行
            executed_orders = []
            for order in orders:
                is_valid, message = risk_manager.validate_trade(
                    order['symbol'],
                    order['side'],
                    order['amount']
                )
                
                if is_valid:
                    logger.info(f"Executing {order['side']} order for {order['symbol']}: {order['amount']}")
                    result = gateio_client.create_market_order(
                        order['symbol'],
                        order['side'],
                        order['amount']
                    )
                    
                    if result:
                        # 取引履歴を保存
                        dynamodb_client.save_transaction(
                            order['symbol'],
                            order['side'],
                            order['amount'],
                            result.get('price', 0),
                            result.get('status', 'unknown'),
                            current_allocations,
                            target_allocations
                        )
                        executed_orders.append(result)
                else:
                    logger.warning(f"Trade validation failed for {order['symbol']}: {message}")
            
            # 7. 判断履歴を保存
            dynamodb_client.save_judgment(
                confidence_score,
                reasoning,
                target_allocations,
                news_data['source_urls'],
                news_data['fetch_status'],
                news_data['failed_sources']
            )
        else:
            logger.info(f"Confidence Score ({confidence_score}) below threshold ({MIN_CONFIDENCE_SCORE}), skipping action")
            # 判断履歴のみ保存（アクションなし）
            target_allocations = current_allocations
            dynamodb_client.save_judgment(
                confidence_score,
                reasoning,
                target_allocations,
                news_data['source_urls'],
                news_data['fetch_status'],
                news_data['failed_sources']
            )
        
        # 8. ポートフォリオスナップショットを保存
        holdings = {symbol: balance.get(symbol, 0) for symbol in TRADING_SYMBOLS + ['USDT']}
        values_usdt = {}
        for symbol in TRADING_SYMBOLS:
            if symbol in balance and balance[symbol] > 0:
                values_usdt[symbol] = balance[symbol] * tickers.get(symbol, {}).get('price', 0)
        if 'USDT' in balance:
            values_usdt['USDT'] = balance['USDT']
        
        final_allocations = calculate_current_allocations(balance, tickers)
        dynamodb_client.save_portfolio_snapshot(
            holdings,
            values_usdt,
            total_value,
            final_allocations
        )
        
        logger.info("Execution completed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Execution completed successfully',
                'confidence_score': confidence_score,
                'orders_executed': len(executed_orders) if confidence_score >= MIN_CONFIDENCE_SCORE else 0
            })
        }
    
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")
        raise
    
    finally:
        # ロック解放
        release_lock()

