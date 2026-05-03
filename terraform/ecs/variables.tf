variable "terraform_execution_role_arn" {
  description = "The ARN of the IAM role that Terraform will assume to create resources"
  type        = string
}

variable "image_tag" {
  type        = string
  description = "The tag of the image to deploy"
  default     = "latest"
}

variable "bucket_name" {
  description = "The unique name of the S3 bucket where reports are stored"
  type        = string
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

variable "av_api_key" {
  description = "Alpha Vantage API key used by the report collector"
  type        = string
  sensitive   = true
}





