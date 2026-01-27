variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "table_prefix" {
  description = "DynamoDB table prefix"
  type        = string
  default     = "rwa_trading_agent"
}

variable "gateio_api_key" {
  description = "Gate.io API Key"
  type        = string
  sensitive   = true
}

variable "gateio_api_secret" {
  description = "Gate.io API Secret"
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Gemini API Key"
  type        = string
  sensitive   = true
}
