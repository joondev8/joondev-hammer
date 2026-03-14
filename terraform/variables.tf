variable "terraform_execution_role_arn" {
  description = "The ARN of the IAM role that Terraform will assume to create resources"
  type        = string
}

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

variable "db_name" {
  type      = string
  sensitive = true
}

variable "db_host" {
  type      = string
  sensitive = true
}

variable "db_port" {
  type    = number
  default = 5432
}

variable "db_username" {
  type      = string
  sensitive = true
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "db_schema" {
  type    = string
  default = "market_data"
}

variable "db_sslmode" {
  type    = string
  default = "require"
}

# variable "lambda_vpc_id" {
#   description = "VPC ID where ticker_loader Lambda should run to reach private RDS"
#   type        = string
#   default     = ""
# }

# variable "lambda_subnet_ids" {
#   description = "Private subnet IDs for ticker_loader Lambda ENIs"
#   type        = list(string)
#   default     = []
# }

# variable "private_route_table_ids" {
#   description = "Private route table IDs for the VPC endpoint"
#   type        = list(string)
#   default     = []
# }

# variable "db_security_group_id" {
#   description = "Security group ID attached to the PostgreSQL instance"
#   type        = string
#   default     = ""
# }