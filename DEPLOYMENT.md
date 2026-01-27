# デプロイメントガイド

このドキュメントでは、RWA Trading AgentをAWSにデプロイする手順を説明します。

## 前提条件

- AWSアカウントがあること
- AWS CLIがインストール・設定されていること
- Terraformがインストールされていること（バージョン1.0以上）
- Gate.io APIキーとシークレットを取得済み
- Gemini APIキーを取得済み

## デプロイ手順

### 1. AWS認証情報の設定

AWS CLIを使用して認証情報を設定します：

```bash
aws configure
```

または、環境変数で設定：

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=ap-northeast-1
```

### 2. Terraform変数ファイルの作成

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars`を編集して、APIキーを設定：

```hcl
aws_region = "ap-northeast-1"
table_prefix = "rwa_trading_agent"

gateio_api_key = "your_actual_gateio_api_key"
gateio_api_secret = "your_actual_gateio_api_secret"
gemini_api_key = "your_actual_gemini_api_key"
```

**重要**: `terraform.tfvars`は`.gitignore`に含まれているため、Gitにコミットされません。

### 3. Terraformの初期化とデプロイ

```bash
# Terraformを初期化
terraform init

# プランを確認（作成されるリソースを確認）
terraform plan

# デプロイ実行
terraform apply
```

確認プロンプトで`yes`と入力すると、リソースが作成されます。

### 4. デプロイ完了後の確認

デプロイが完了すると、以下の情報が表示されます：

```
Outputs:

api_gateway_url = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com"
lambda_function_name = "rwa_trading_agent-main"
api_lambda_function_name = "rwa_trading_agent-api"
```

### 5. フロントエンドの設定（ローカル開発時）

フロントエンドをローカルで実行する場合、API Gateway URLを設定します：

```bash
cd frontend
cp .env.example .env
```

`.env`ファイルを編集して、`api_gateway_url`を設定：

```bash
VITE_API_BASE_URL=https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com
```

### 6. 動作確認

#### Lambda関数の動作確認

AWS Lambdaコンソールで、`rwa_trading_agent-main`関数を確認：
- 関数が正常に作成されているか
- 環境変数が正しく設定されているか
- EventBridgeルールが正しく設定されているか

#### API Gatewayの動作確認

```bash
# ヘルスチェック
curl https://your-api-gateway-url.execute-api.ap-northeast-1.amazonaws.com/health

# ポートフォリオ情報取得
curl https://your-api-gateway-url.execute-api.ap-northeast-1.amazonaws.com/api/portfolio/current
```

## トラブルシューティング

### Lambda関数のデプロイエラー

**問題**: ZIPファイルが大きすぎる（50MB以上）

**解決策**: S3バケットを使用するようにTerraform設定を変更する必要があります。

### API GatewayのCORSエラー

**問題**: フロントエンドからAPI Gatewayにアクセスする際にCORSエラーが発生

**解決策**: `infrastructure/terraform/main.tf`の`cors_configuration`を確認してください。既に`allow_origins = ["*"]`に設定されているはずです。

### DynamoDBテーブルの作成エラー

**問題**: テーブル名が既に存在する

**解決策**: 
- 既存のテーブルを削除する
- または、`terraform.tfvars`の`table_prefix`を変更する

### Lambda関数のタイムアウト

**問題**: Lambda関数がタイムアウトする

**解決策**: 
- `infrastructure/terraform/main.tf`の`timeout`を増やす（現在は300秒=5分）
- または、処理を最適化する

### EventBridgeルールが実行されない

**問題**: Lambda関数が5分間隔で実行されない

**解決策**:
1. AWS EventBridgeコンソールでルールが有効になっているか確認
2. Lambda関数のCloudWatch Logsを確認してエラーがないか確認
3. IAMロールの権限を確認

## リソースの削除

すべてのリソースを削除する場合：

```bash
cd infrastructure/terraform
terraform destroy
```

**警告**: これにより、すべてのリソースが削除されます。DynamoDBテーブルのデータも失われます。

## 更新手順

コードを更新した場合：

```bash
cd infrastructure/terraform
terraform apply
```

Terraformが変更を検出し、Lambda関数を自動的に更新します。

## コスト見積もり

### 月額コスト（概算）

- **DynamoDB**: オンデマンド課金（使用量に応じて）
- **Lambda**: 無料枠（100万リクエスト/月）を超えると課金
- **EventBridge**: 無料枠（100万イベント/月）を超えると課金
- **API Gateway**: HTTP APIは100万リクエスト/月まで無料

**注意**: 実際のコストは使用量によって異なります。AWS Pricing Calculatorで詳細を確認してください。
