# Terraform Infrastructure

このディレクトリには、RWA Trading AgentのAWSインフラストラクチャを定義するTerraform設定ファイルが含まれています。

## セットアップ

### 1. Terraformのインストール

Terraformがインストールされていない場合は、[公式サイト](https://www.terraform.io/downloads)からインストールしてください。

### 2. AWS認証情報の設定

以下のいずれかの方法でAWS認証情報を設定してください：

#### 方法1: 環境変数
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=ap-northeast-1
```

#### 方法2: AWS CLI設定
```bash
aws configure
```

### 3. 変数ファイルの作成

```bash
cp terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars`を編集して、APIキーを設定してください：

```hcl
aws_region = "ap-northeast-1"
table_prefix = "rwa_trading_agent"

gateio_api_key = "your_actual_gateio_api_key"
gateio_api_secret = "your_actual_gateio_api_secret"
gemini_api_key = "your_actual_gemini_api_key"
auth_token = "your_actual_cryptopanic_auth_token"
```

**重要**: `terraform.tfvars`は`.gitignore`に含まれているため、Gitにコミットされません。

### 4. Terraformの初期化

```bash
terraform init
```

### 5. プランの確認

```bash
terraform plan
```

これにより、作成されるリソースの一覧が表示されます。

### 6. デプロイ

```bash
terraform apply
```

確認プロンプトで`yes`と入力すると、リソースが作成されます。

### 7. 出力の確認

デプロイが完了すると、以下の情報が表示されます：

- `api_gateway_url`: API GatewayのエンドポイントURL
- `lambda_function_name`: メイン実行Lambda関数の名前
- `api_lambda_function_name`: API Lambda関数の名前

## 作成されるリソース

- **DynamoDBテーブル** (5つ)
  - `{prefix}_judgments`: 判断履歴
  - `{prefix}_transactions`: 取引履歴
  - `{prefix}_portfolio_snapshots`: 資産スナップショット
  - `{prefix}_price_history`: 価格履歴
  - `{prefix}_execution_locks`: 実行ロック

- **Lambda関数** (2つ)
  - `{prefix}-main`: メイン実行サイクル（5分間隔で実行）
  - `{prefix}-api`: API Gateway用のバックエンド

- **EventBridgeルール**
  - `{prefix}-5min-schedule`: 5分間隔でメインLambda関数を実行

- **API Gateway**
  - HTTP API: フロントエンドからアクセス可能

- **IAMロールとポリシー**
  - Lambda関数用の実行ロールとDynamoDBアクセス権限

## リソースの削除

```bash
terraform destroy
```

**注意**: これにより、すべてのリソースが削除されます。DynamoDBテーブルのデータも失われます。

## トラブルシューティング

### Lambda関数のデプロイエラー

Lambda関数のZIPファイルが大きすぎる場合（50MB以上）、S3を使用する必要があります。その場合は、`main.tf`を修正してS3バケットを使用するようにしてください。

### API GatewayのCORSエラー

フロントエンドからAPI Gatewayにアクセスする際にCORSエラーが発生する場合は、`main.tf`の`cors_configuration`を確認してください。

### DynamoDBテーブルの作成エラー

テーブル名が既に存在する場合は、エラーが発生します。既存のテーブルを削除するか、`table_prefix`を変更してください。
