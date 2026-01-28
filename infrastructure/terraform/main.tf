terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# IAMロール（メイン実行Lambda用）
resource "aws_iam_role" "trading_agent_lambda_role" {
  name = "${var.table_prefix}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "trading_agent_lambda_basic" {
  role       = aws_iam_role.trading_agent_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "trading_agent_lambda_dynamodb" {
  name = "${var.table_prefix}-lambda-dynamodb-policy"
  role = aws_iam_role.trading_agent_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.judgments.arn,
          aws_dynamodb_table.transactions.arn,
          aws_dynamodb_table.portfolio_snapshots.arn,
          aws_dynamodb_table.price_history.arn,
          aws_dynamodb_table.execution_locks.arn
        ]
      }
    ]
  })
}

# IAMロール（API Lambda用）
resource "aws_iam_role" "api_lambda_role" {
  name = "${var.table_prefix}-api-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_lambda_basic" {
  role       = aws_iam_role.api_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "api_lambda_dynamodb" {
  name = "${var.table_prefix}-api-lambda-dynamodb-policy"
  role = aws_iam_role.api_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.judgments.arn,
          aws_dynamodb_table.transactions.arn,
          aws_dynamodb_table.portfolio_snapshots.arn,
          aws_dynamodb_table.price_history.arn
        ]
      }
    ]
  })
}

# DynamoDBテーブル
resource "aws_dynamodb_table" "judgments" {
  name           = "${var.table_prefix}_judgments"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "judgment_id"
  range_key      = "timestamp"

  attribute {
    name = "judgment_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  global_secondary_index {
    name            = "judgments_by_timestamp"
    hash_key        = "judgment_id"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.table_prefix}-judgments"
  }
}

resource "aws_dynamodb_table" "transactions" {
  name           = "${var.table_prefix}_transactions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "transaction_id"
  range_key      = "timestamp"

  attribute {
    name = "transaction_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "symbol"
    type = "S"
  }

  global_secondary_index {
    name            = "transactions_by_symbol"
    hash_key        = "symbol"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.table_prefix}-transactions"
  }
}

resource "aws_dynamodb_table" "portfolio_snapshots" {
  name           = "${var.table_prefix}_portfolio_snapshots"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "snapshot_id"
  range_key      = "timestamp"

  attribute {
    name = "snapshot_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  global_secondary_index {
    name            = "portfolio_snapshots_by_timestamp"
    hash_key        = "snapshot_id"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.table_prefix}-portfolio-snapshots"
  }
}

resource "aws_dynamodb_table" "price_history" {
  name         = "${var.table_prefix}_price_history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "symbol"
  range_key    = "timestamp"

  attribute {
    name = "symbol"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Name = "${var.table_prefix}-price-history"
  }
}

resource "aws_dynamodb_table" "execution_locks" {
  name         = "${var.table_prefix}_execution_locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "lock_id"

  attribute {
    name = "lock_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Name = "${var.table_prefix}-execution-locks"
  }
}

# S3バケット（Lambda関数のデプロイパッケージ用）
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "lambda_deployments" {
  bucket = "${replace(var.table_prefix, "_", "-")}-lambda-deployments-${random_id.bucket_suffix.hex}"

  tags = {
    Name = "${replace(var.table_prefix, "_", "-")}-lambda-deployments"
  }
}

resource "aws_s3_bucket_versioning" "lambda_deployments" {
  bucket = aws_s3_bucket.lambda_deployments.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3オブジェクト（メインLambda関数用）
resource "aws_s3_object" "trading_agent_lambda" {
  depends_on = [data.archive_file.trading_agent_lambda]
  bucket     = aws_s3_bucket.lambda_deployments.id
  key        = "lambda-${data.archive_file.trading_agent_lambda.output_base64sha256}.zip"
  source     = data.archive_file.trading_agent_lambda.output_path
  etag       = data.archive_file.trading_agent_lambda.output_md5
}

# S3オブジェクト（API Lambda関数用）
resource "aws_s3_object" "api_lambda" {
  depends_on = [data.archive_file.api_lambda]
  bucket     = aws_s3_bucket.lambda_deployments.id
  key        = "api-${data.archive_file.api_lambda.output_base64sha256}.zip"
  source     = data.archive_file.api_lambda.output_path
  etag       = data.archive_file.api_lambda.output_md5
}

# Lambda Layer用の依存関係をインストール
resource "null_resource" "lambda_layer_package" {
  triggers = {
    requirements_hash = filesha256("${path.module}/../../lambda-layer/requirements.txt")
    python_version = "3.13"
    runtime_version = "python3.13"
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.module}/../../lambda-layer
      # クリーンアップ
      rm -rf python/*.dist-info python/__pycache__ python/*/__pycache__
      find python -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
      find python -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
      # Lambda Layer用のLinux互換パッケージをインストール
      python3 -m pip install -r requirements.txt -t python --upgrade \
        --platform manylinux2014_x86_64 \
        --only-binary=:all: \
        --python-version 3.13 \
        --implementation cp \
        --quiet \
        --disable-pip-version-check
    EOT
  }
}

# Lambda Layer用のZIPファイル
data "archive_file" "lambda_layer" {
  depends_on = [null_resource.lambda_layer_package]
  type       = "zip"
  source_dir = "${path.module}/../../lambda-layer"
  output_path = "${path.module}/lambda-layer.zip"
  excludes    = ["__pycache__", "*.pyc", "*.log"]
}

# Lambda Layer用のS3オブジェクト
resource "aws_s3_object" "lambda_layer" {
  depends_on = [data.archive_file.lambda_layer]
  bucket     = aws_s3_bucket.lambda_deployments.id
  key        = "layer-${data.archive_file.lambda_layer.output_base64sha256}.zip"
  source     = data.archive_file.lambda_layer.output_path
  etag       = data.archive_file.lambda_layer.output_md5
}

# Lambda Layer
resource "aws_lambda_layer_version" "dependencies" {
  layer_name          = "${var.table_prefix}-dependencies"
  s3_bucket           = aws_s3_bucket.lambda_deployments.id
  s3_key              = aws_s3_object.lambda_layer.key
  compatible_runtimes = ["python3.13"]

  source_code_hash = data.archive_file.lambda_layer.output_base64sha256
}

# Lambda関数（メイン実行用）- 依存関係を含むZIPを作成
resource "null_resource" "trading_agent_lambda_package" {
  triggers = {
    source_hash = sha256(join("", [
      for f in fileset("${path.module}/../../lambda", "**/*.py") : filesha256("${path.module}/../../lambda/${f}")
    ]))
    requirements_hash = filesha256("${path.module}/../../lambda/requirements.txt")
    python_version = "3.13"
    runtime_version = "python3.13"
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.module}/../../lambda
      # クリーンアップ: 以前のデプロイで残っている依存関係を削除
      rm -rf *.dist-info __pycache__ */__pycache__ */*/__pycache__
      find . -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
      find . -type d -name "__pycache__" -not -path "./venv/*" -exec rm -rf {} + 2>/dev/null || true
      # Lambda用のLinux互換パッケージをインストール
      python3 -m pip install -r requirements.txt -t . --upgrade \
        --platform manylinux2014_x86_64 \
        --only-binary=:all: \
        --python-version 3.13 \
        --implementation cp \
        --quiet \
        --disable-pip-version-check
    EOT
  }
}

data "archive_file" "trading_agent_lambda" {
  depends_on = [null_resource.trading_agent_lambda_package]
  type       = "zip"
  source_dir = "${path.module}/../../lambda"
  output_path = "${path.module}/lambda.zip"
  excludes    = ["__pycache__", "*.pyc", ".env", "*.zip", "package", "*.log"]
}

resource "aws_lambda_function" "trading_agent" {
  s3_bucket        = aws_s3_bucket.lambda_deployments.id
  s3_key           = aws_s3_object.trading_agent_lambda.key
  function_name    = "${var.table_prefix}-main"
  role            = aws_iam_role.trading_agent_lambda_role.arn
  handler         = "main.lambda_handler"
  runtime         = "python3.13"
  timeout         = 300
  memory_size     = 512

  source_code_hash = data.archive_file.trading_agent_lambda.output_base64sha256

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      GATEIO_API_KEY    = var.gateio_api_key
      GATEIO_API_SECRET = var.gateio_api_secret
      GEMINI_API_KEY    = var.gemini_api_key
      DYNAMODB_TABLE_PREFIX = var.table_prefix
    }
  }

  tags = {
    Name = "${var.table_prefix}-main"
  }
}

# Lambda関数（API用）- 依存関係を含むZIPを作成
resource "null_resource" "api_lambda_package" {
  triggers = {
    source_hash = sha256(join("", [
      for f in fileset("${path.module}/../../backend", "**/*.py") : filesha256("${path.module}/../../backend/${f}")
    ]))
    requirements_hash = filesha256("${path.module}/../../backend/requirements.txt")
    python_version = "3.13"
    runtime_version = "python3.13"
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.module}/../../backend
      # クリーンアップ: 以前のデプロイで残っている依存関係を削除
      rm -rf *.dist-info __pycache__ */__pycache__ */*/__pycache__
      find . -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
      find . -type d -name "__pycache__" -not -path "./venv/*" -exec rm -rf {} + 2>/dev/null || true
      # Lambda用のLinux互換パッケージをインストール
      python3 -m pip install -r requirements.txt -t . --upgrade \
        --platform manylinux2014_x86_64 \
        --only-binary=:all: \
        --python-version 3.13 \
        --implementation cp \
        --quiet \
        --disable-pip-version-check
    EOT
  }
}

data "archive_file" "api_lambda" {
  depends_on = [null_resource.api_lambda_package]
  type       = "zip"
  source_dir = "${path.module}/../../backend"
  output_path = "${path.module}/api.zip"
  excludes    = ["__pycache__", "*.pyc", ".env", "*.zip", "package", "*.log"]
}

resource "aws_lambda_function" "api" {
  s3_bucket        = aws_s3_bucket.lambda_deployments.id
  s3_key           = aws_s3_object.api_lambda.key
  function_name    = "${var.table_prefix}-api"
  role            = aws_iam_role.api_lambda_role.arn
  handler         = "app.main.handler"
  runtime         = "python3.13"
  timeout         = 30
  memory_size     = 256

  source_code_hash = data.archive_file.api_lambda.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_PREFIX = var.table_prefix
    }
  }

  tags = {
    Name = "${var.table_prefix}-api"
  }
}

# EventBridgeルール
resource "aws_cloudwatch_event_rule" "trading_agent_schedule" {
  name                = "${var.table_prefix}-30min-schedule"
  description         = "RWA Trading Agent execution schedule (test mode: 30 minutes)"
  schedule_expression = "rate(30 minutes)"

  tags = {
    Name = "${var.table_prefix}-schedule"
  }
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.trading_agent_schedule.name
  target_id = "TriggerTradingAgentLambda"
  arn       = aws_lambda_function.trading_agent.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trading_agent.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trading_agent_schedule.arn
}

# API Gateway
resource "aws_apigatewayv2_api" "api" {
  name          = "${var.table_prefix}-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["*"]
    allow_headers = ["*"]
  }

  tags = {
    Name = "${var.table_prefix}-api"
  }
}

resource "aws_apigatewayv2_integration" "api" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri   = aws_lambda_function.api.invoke_arn
}

resource "aws_apigatewayv2_route" "api" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

resource "aws_apigatewayv2_stage" "api" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "allow_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

# 出力
output "api_gateway_url" {
  description = "API Gateway URL"
  value       = aws_apigatewayv2_api.api.api_endpoint
}

output "lambda_function_name" {
  description = "Trading Agent Lambda function name"
  value       = aws_lambda_function.trading_agent.function_name
}

output "api_lambda_function_name" {
  description = "API Lambda function name"
  value       = aws_lambda_function.api.function_name
}
