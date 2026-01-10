# RWA Trading Agent システム仕様書

## 1. システム概要

### 1.1 コンセプト

「世界の動きと市場の不一致を突く先回り型エージェント」

- 土日や深夜など伝統的市場が閉まっている時間帯の経済ニュースをLLM（Gemini 3 Flash）が解析
- Gate.ioで24時間取引可能なRWA（現実資産トークン）へ、他のトレーダーが気づく前に資産を配分
- 5分間隔で自律的に実行（AWS EventBridgeで固定スケジュール実行）

### 1.2 技術スタック

- **言語**: Python 3.10+
- **LLM**: Gemini 3 Flash (Google AI SDK `google-genai`)
- **Exchange API**: Gate.io API V4 (`ccxt` ライブラリ)
- **バックエンド**: FastAPI
- **フロントエンド**: React (TypeScript)
- **データベース**: DynamoDB
- **実行環境**: AWS Lambda
- **スケジューラー**: AWS EventBridge (CloudWatch Events)
- **設定管理**: `.env` ファイル

## 2. 取引対象資産

Gate.ioで扱われる以下のシンボルを監視・取引対象とする：

- **貴金属**: `PAXG/USDT` (Gold), `KAG/USDT` (Silver)
- **株式指数**: `SPYON/USDT` (S&P500), `QQQON/USDT` (NASDAQ)
- **個別株**: `TSLAX/USDT` (Tesla), `NVDAX/USDT` (NVIDIA), `MSTRX/USDT` (MicroStrategy)
- **法定通貨**: `EURS/USDT` (Euro), `GBPT/USDT` (Pound)
- **債券**: `ONDO/USDT` (US Treasury)

## 3. システムアーキテクチャ

### 3.1 コンポーネント構成

```
┌─────────────────┐
│  React管理画面   │
│  (TypeScript)   │
└────────┬────────┘
         │ HTTP (画面リロード時)
         ▼
┌─────────────────┐
│  FastAPI        │
│  (Backend API)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│DynamoDB│ │AWS Lambda│
└────────┘ └────┬─────┘
                │
         ┌──────┴──────┐
         │             │
         ▼             ▼
    ┌────────┐    ┌─────────┐
    │Gate.io │    │Gemini   │
    │API     │    │API      │
    └────────┘    └─────────┘
         │
         ▼
┌─────────────────┐
│  EventBridge    │
│  (5分間隔)      │
└─────────────────┘
```

### 3.2 データフロー

1. **EventBridge** (5分間隔で固定スケジュール)
   - Lambda関数を自動的にトリガー

2. **Lambda関数** (5分間隔で実行)
   - ニュース収集 → Gemini分析 → ポートフォリオ最適化 → Gate.io取引実行 → DynamoDB保存

3. **FastAPI** (常時稼働)
   - 管理画面からのリクエストを受け付け、DynamoDBからデータを取得して返却

4. **React管理画面** (画面リロード時更新)
   - 画面リロード時にFastAPIを呼び出し、最新の資産状況・判断履歴・取引履歴を表示

## 4. 実行サイクル (Agentic Workflow)

### 4.1 メインサイクル（5分間隔）

1. **情報収集 (Scraping)**
   - 経済ニュースサイトからテキストを抽出
   - 優先順位: API → スクレイピング（フォールバック）
   - 対象ソース:
     - ロイター (Reuters) - Business: https://www.reuters.com/business/
     - Investing.com: https://jp.investing.com/news/general
     - CryptoPanic API: https://cryptopanic.com/about/api/
     - CoinDesk Japan: https://www.coindeskjapan.com/
     - ForexFactory: https://www.forexfactory.com/calendar
     - Liveuamap: https://liveuamap.com/

2. **市場分析 (Reasoning)**
   - Gemini 3 Flashが「ニュースの内容」と「現在のGate.ioの価格/騰落率」を比較
   - **Confidence Score (1-10)** を算出
   - 8以上の場合のみアクションを検討

3. **ポートフォリオ最適化**
   - LLMが目標資産比率（例: PAXG 60%, USDT 40%）を決定
   - 既存資産との差分を計算し、最小限の売買命令を生成

4. **リスク管理チェック**
   - スプレッドフィルター: 板（Order Book）を確認し、スプレッドが0.5%以上の場合はエントリーをスキップ
   - 端数処理: 全額両替時の手数料（0.2%〜）を考慮し、残高の99.8%で計算
   - デペグ防止: 週末の価格が直近終値から大きく乖離（5%以上）している場合、エントリーを制限

5. **実行 (Execution)**
   - Gate.io APIを通じて成行注文を発注
   - 取引結果をDynamoDBに保存

6. **ログ記録 (Reflect)**
   - 「なぜその判断をしたか」の推論プロセスをDynamoDBに保存
   - 判断根拠テキスト、参考URL、情報取得成否を記録

### 4.2 実行スケジュール

- AWS EventBridge (CloudWatch Events) を使用して5分間隔で固定スケジュール実行
- EventBridgeルール: `rate(5 minutes)` で設定
- EventBridgeルールがLambda関数を自動的にトリガー
- Lambda関数にEventBridgeからの実行権限を付与

## 5. データベース設計 (DynamoDB)

### 5.1 テーブル構成

#### 5.1.1 `judgments` (判断履歴)

- **Partition Key**: `judgment_id` (UUID)
- **Sort Key**: `timestamp` (ISO 8601)
- **Attributes**:
  - `confidence_score` (Number)
  - `target_allocations` (Map: シンボル → 割合%)
  - `reasoning_text` (String)
  - `source_urls` (List of String)
  - `info_fetch_status` (Map: ソース名 → 成否)
  - `failed_sources` (List of String)

#### 5.1.2 `transactions` (取引履歴)

- **Partition Key**: `transaction_id` (UUID)
- **Sort Key**: `timestamp` (ISO 8601)
- **Attributes**:
  - `symbol` (String: 例 "PAXG/USDT")
  - `side` (String: "buy" or "sell")
  - `amount` (Number)
  - `price` (Number)
  - `status` (String: "success" or "failed")
  - `pre_allocation` (Map: シンボル → 割合%)
  - `post_allocation` (Map: シンボル → 割合%)

#### 5.1.3 `portfolio_snapshots` (資産スナップショット)

- **Partition Key**: `snapshot_id` (UUID)
- **Sort Key**: `timestamp` (ISO 8601)
- **Attributes**:
  - `holdings` (Map: シンボル → 数量)
  - `values_usdt` (Map: シンボル → USDT価値)
  - `total_value_usdt` (Number)
  - `allocations` (Map: シンボル → 割合%)

#### 5.1.4 `price_history` (価格履歴)

- **Partition Key**: `symbol` (String: 例 "PAXG/USDT")
- **Sort Key**: `timestamp` (ISO 8601)
- **Attributes**:
  - `price` (Number)
  - `change_24h` (Number: %)
  - `volume` (Number)

### 5.2 GSI (Global Secondary Index)

- `judgments_by_timestamp`: `timestamp` をソートキーとして時系列クエリ
- `transactions_by_symbol`: `symbol` をパーティションキー、`timestamp` をソートキー
- `portfolio_snapshots_by_timestamp`: `timestamp` をソートキーとして時系列クエリ

## 6. API設計 (FastAPI)

### 6.1 エンドポイント

#### 6.1.1 資産情報

- `GET /api/portfolio/current` - 現在の資産内訳
- `GET /api/portfolio/performance` - 騰落率（1日/2日/1週間/2週間/1ヶ月）
- `GET /api/portfolio/currency-performance` - 各通貨の騰落率

#### 6.1.2 判断履歴

- `GET /api/judgments` - 判断履歴一覧（ページネーション対応）
- `GET /api/judgments/{judgment_id}` - 特定の判断詳細

#### 6.1.3 取引履歴

- `GET /api/transactions` - 取引履歴一覧（ページネーション対応）
- `GET /api/transactions/{transaction_id}` - 特定の取引詳細

### 6.2 レスポンス形式

- JSON形式
- エラーハンドリング: HTTPステータスコード + エラーメッセージ

## 7. 管理画面 (React + TypeScript)

### 7.1 画面構成

#### 7.1.1 ダッシュボード

- 資産内訳（円グラフ/テーブル）
- 資産全体の騰落率
  - 過去1日
  - 過去2日
  - 過去1週間
  - 過去2週間
  - 過去1ヶ月
- 各通貨の騰落率（テーブル/グラフ）

#### 7.1.2 判断履歴画面

- 判断日時
- 判断結果（各通貨毎の持つべき割合）
- 判断根拠
  - 判断根拠テキストによる説明
  - 判断根拠で参考にしたURL（複数）
- 根拠情報取得成否
  - 成否
  - 取得失敗した情報源（もしあれば）

#### 7.1.3 取引履歴画面

- 取引日時
- 取引通貨
- 取引数量
- 成否
- 取引前資産割合
- 取引後資産割合

### 7.2 データ更新

- 画面リロード時に最新データを取得
- 自動リフレッシュ機能は不要

## 8. 最適化技術

### 8.1 Context Caching

- システムプロンプト（運用ルール、資産定義、API指示）が32kトークンを超える場合は、Google Cloud Vertex AI / Gemini API のキャッシュ機能を使用し、コストを90%削減

### 8.2 エラーハンドリング

- ネットワークエラー時のリトライロジック
- API制限エラー時のバックオフ戦略
- 取引失敗時のロールバック処理
- Lambda実行タイムアウト: 5分に設定（実行サイクルが完了する時間を確保）
- 同時実行制御: DynamoDBでロック機構を実装し、前回実行が完了するまで次回実行をスキップ

## 9. セキュリティ・設定管理

### 9.1 環境変数 (.env)

- `GATEIO_API_KEY` - Gate.io APIキー
- `GATEIO_API_SECRET` - Gate.io APIシークレット
- `GEMINI_API_KEY` - Gemini APIキー
- `AWS_ACCESS_KEY_ID` - AWSアクセスキー
- `AWS_SECRET_ACCESS_KEY` - AWSシークレットキー
- `AWS_REGION` - AWSリージョン
- `DYNAMODB_TABLE_PREFIX` - DynamoDBテーブル名プレフィックス（オプション）

### 9.2 認証

- 管理画面: 認証不要（必要に応じて後で追加可能）

## 10. ログ管理

### 10.1 データベース保存

- 取引ログ: `transactions` テーブル
- 判断ログ: `judgments` テーブル

### 10.2 ログファイル

- デバッグログ: ファイル出力（JSON形式推奨）
- ログレベル: DEBUG, INFO, WARNING, ERROR
- ローテーション: 日次またはサイズベース

## 11. デプロイ構成 (AWS)

### 11.1 Lambda関数

- メイン実行サイクル用のLambda関数
- EventBridge (CloudWatch Events) で5分間隔で固定スケジュール実行
- EventBridgeルール: `rate(5 minutes)` で設定
- Lambda関数にEventBridgeからの実行権限を付与
- Lambda実行タイムアウト: 5分
- Lambdaメモリ: 512MB以上推奨（Gemini API呼び出しとニュース処理のため）

### 11.2 EventBridge設定

- EventBridgeルール名: `trading-agent-5min-schedule`
- スケジュール式: `rate(5 minutes)`
- ターゲット: Lambda関数
- Lambda関数への実行権限を付与

### 11.3 FastAPI

- EC2またはECS/Fargateで常時稼働
- またはAPI Gateway + Lambda（サーバーレス構成）
- CORS設定: React管理画面からのアクセスを許可

### 11.4 React管理画面

- S3 + CloudFrontでホスティング
- またはAmplifyでデプロイ
- TypeScriptで実装

## 12. 開発フェーズ

### Phase 1: コア機能

- Lambda関数: ニュース収集 → Gemini分析 → ポートフォリオ最適化
- Gate.io API連携: 残高取得、価格取得
- DynamoDB: テーブル作成、データ保存
- EventBridge: スケジュール設定とLambda連携

### Phase 2: 取引実行

- リスク管理ロジック実装
- 成行注文実行
- 取引履歴保存
- 同時実行制御（DynamoDBロック機構）

### Phase 3: 管理画面

- FastAPI実装
- React管理画面実装（TypeScript）
- データ可視化（グラフ・チャート）

### Phase 4: 最適化・運用

- Context Caching実装
- エラーハンドリング強化
- ログ・モニタリング整備
- EventBridge設定とLambdaデプロイ
- CloudWatchアラーム設定

## 13. EventBridge実装詳細

### 13.1 EventBridgeルール設定

```json
{
  "Name": "trading-agent-5min-schedule",
  "Description": "RWA Trading Agent execution schedule",
  "ScheduleExpression": "rate(5 minutes)",
  "State": "ENABLED",
  "Targets": [
    {
      "Id": "TriggerTradingAgentLambda",
      "Arn": "arn:aws:lambda:REGION:ACCOUNT:function:trading-agent-main"
    }
  ]
}
```

### 13.2 Lambda関数の権限設定

- EventBridgeがLambda関数を呼び出すための権限が必要
- IAMロールに`lambda:InvokeFunction`権限を付与

### 13.3 Lambda関数の実装構造

```python
def lambda_handler(event, context):
    """
    メイン実行サイクル
    EventBridgeから5分間隔で呼び出される
    """
    try:
        # 1. 情報収集
        news_data = collect_news()
        
        # 2. 市場分析
        confidence_score, reasoning = analyze_market(news_data)
        
        # 3. ポートフォリオ最適化
        if confidence_score >= 8:
            target_allocations = optimize_portfolio(reasoning)
            
            # 4. リスク管理チェック
            if risk_check_passed():
                # 5. 実行
                execute_trades(target_allocations)
        
        # 6. ログ記録
        save_judgment(confidence_score, reasoning, target_allocations)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Execution completed successfully')
        }
    except Exception as e:
        # エラーログを記録
        logger.error(f"Execution failed: {str(e)}")
        raise
```

## 14. 同時実行制御

### 14.1 DynamoDBロック機構

- Lambda関数実行開始時にDynamoDBにロックレコードを作成
- 実行完了時にロックを解除
- 次回実行時にロックが存在する場合は実行をスキップ
- ロックテーブル: `execution_locks`
  - Partition Key: `lock_id` (固定値: "main_execution")
  - Attributes: `locked_at` (ISO 8601), `expires_at` (ISO 8601)
  - TTL: `expires_at` を設定（例: 10分後）

### 14.2 実装例

```python
def acquire_lock():
    """実行ロックを取得"""
    try:
        lock_table.put_item(
            Item={
                'lock_id': 'main_execution',
                'locked_at': datetime.utcnow().isoformat(),
                'expires_at': int((datetime.utcnow() + timedelta(minutes=10)).timestamp())
            },
            ConditionExpression='attribute_not_exists(lock_id)'
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False  # 既にロックされている
        raise

def release_lock():
    """実行ロックを解放"""
    lock_table.delete_item(Key={'lock_id': 'main_execution'})
```

