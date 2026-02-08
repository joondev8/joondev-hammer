variable "bucket_name" {
  description = "The unique name of the S3 bucket where reports are stored"
  type        = string
}

variable "support_email" {
  description = "The email address that receives failure alerts"
  type        = string
}

# Optional: You can also declare your region here
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}