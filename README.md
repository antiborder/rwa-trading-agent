# RWA Trading Agent

世界の動きと市場の不一致を突く先回り型エージェント

## プロジェクト構成

```
rwa-trading-agent/
├── lambda/                    # Lambda関数
│   ├── main.py               # メイン実行サイクル
│   ├── config.py             # 設定管理
│   ├── utils/                # ユーティリティ
│   │   ├── logger.py
│   │   ├── lock.py
│   │   ├── news_collector.py
│   │   ├── gateio_client.py
│   │   ├── gemini_client.py
│   │   ├── dynamodb_client.py
│   │   └── risk_manager.py
│   └── requirements.txt
├── backend/                  # FastAPI バックエンド
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/              # APIルーター
│   │   │   ├── portfolio.py
│   │   │   ├── judgments.py
│   │   │   └── transactions.py
│   │   ├── models/           # Pydanticスキーマ
│   │   │   └── schemas.py
│   │   └── services/        # サービス層
│   │       └── dynamodb_service.py
│   └── requirements.txt
├── frontend/                 # React (TypeScript) フロントエンド
│   ├── src/
│   │   ├── pages/           # ページコンポーネント
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Judgments.tsx
│   │   │   └── Transactions.tsx
│   │   ├── services/        # APIクライアント
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── infrastructure/           # AWS インフラ設定
│   └── create_tables.py     # DynamoDBテーブル作成スクリプト
├── specification.md          # システム仕様書
└── README.md
```

## セットアップ

### 1. 環境変数の設定

`.env`ファイルを作成し、以下の環境変数を設定してください：

```bash
# Gate.io API
GATEIO_API_KEY=your_gateio_api_key
GATEIO_API_SECRET=your_gateio_api_secret

# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# AWS
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=ap-northeast-1

# DynamoDB
DYNAMODB_TABLE_PREFIX=rwa_trading_agent
```

### 2. DynamoDBテーブルの作成

```bash
cd infrastructure
python create_tables.py
```

### 3. Lambda関数のデプロイ

```bash
cd lambda
pip install -r requirements.txt -t .
zip -r ../lambda.zip .
```

その後、AWS Lambdaコンソールで関数を作成し、`lambda.zip`をアップロードしてください。

### 4. EventBridgeルールの設定

AWS EventBridgeコンソールで以下のルールを作成：

- ルール名: `trading-agent-5min-schedule`
- スケジュール式: `rate(5 minutes)`
- ターゲット: Lambda関数（上記で作成した関数）

### 5. FastAPI バックエンドの起動

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 6. React フロントエンドの起動

```bash
cd frontend
npm install
npm run dev
```

ブラウザで `http://localhost:3000` を開いてください。

## 開発フェーズ

### Phase 1: コア機能 ✅
- Lambda関数: ニュース収集 → Gemini分析 → ポートフォリオ最適化
- Gate.io API連携: 残高取得、価格取得
- DynamoDB: テーブル作成、データ保存

### Phase 2: 取引実行 ✅
- リスク管理ロジック実装
- 成行注文実行
- 取引履歴保存

### Phase 3: 管理画面 ✅
- FastAPI実装
- React管理画面実装（TypeScript）
- データ可視化

### Phase 4: 最適化・運用
- Context Caching実装
- エラーハンドリング強化
- ログ・モニタリング整備
- EventBridge設定とLambdaデプロイ

## API エンドポイント

### ポートフォリオ
- `GET /api/portfolio/current` - 現在の資産内訳
- `GET /api/portfolio/performance` - 騰落率（1日/2日/1週間/2週間/1ヶ月）
- `GET /api/portfolio/currency-performance` - 各通貨の騰落率

### 判断履歴
- `GET /api/judgments` - 判断履歴一覧
- `GET /api/judgments/{judgment_id}` - 特定の判断詳細

### 取引履歴
- `GET /api/transactions` - 取引履歴一覧
- `GET /api/transactions/{transaction_id}` - 特定の取引詳細

## 注意事項

- Gate.io APIキーとGemini APIキーは必ず設定してください
- Lambda関数のタイムアウトは5分に設定してください
- DynamoDBテーブルは事前に作成してください
- EventBridgeルールでLambda関数を5分間隔で実行するように設定してください

