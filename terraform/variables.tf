variable "bucket_name" {
  description = "The unique name of the S3 bucket where reports are stored"
  type        = string
}

variable "support_email" {
  description = "The email address that receives failure alerts"
  type        = string
}

variable "av_api_key" {
  description = "Alpha Vantage API key used by the report generator"
  type        = string
  sensitive   = true
}

# Optional: You can also declare your region here
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "terraform_execution_role_arn" {
  description = "The ARN of the IAM role that Terraform will assume to create resources"
  type        = string
}
variable "av_api_key" {
  description = "API key for Alpha Vantage to fetch stock data"
  type        = string
}

variable "db_path" {
  description = "Database path used by ticker loader Lambda"
  type        = string
  default     = "/tmp/ticker_data.db"
}


variable "db_name" {
  type      = string
  sensitive = true
}

variable "db_username" {
  type      = string
  sensitive = true
}

variable "db_password" {
  type      = string
  sensitive = true
}