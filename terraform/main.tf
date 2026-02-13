# AWS Provider Configuration
provider "aws" {
  region = "us-east-1"
  assume_role {
    # This is the role that Terraform will assume to create resources. Make sure it has the necessary permissions.
    role_arn     = "arn:aws:iam::925369342450:role/TerraformExecutionRole"
    session_name = "TerraformSession"
  }
}

# Create the S3 Bucket
resource "aws_s3_bucket" "report_storage" {
  bucket = var.bucket_name
}

# Automatically zip the source code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/lambda_function.zip"
}

# Lambda Function
resource "aws_lambda_function" "report_gen" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "DailyTickerReportGenerator"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "dailyticker.generate_report.lambda_handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 60  # Increased from the default (3s) to 60 seconds
  memory_size      = 256 # Consider bumping this if the reports are large

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.report_storage.id
    }
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "report_generator_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Permissions Policy (S3 Write + Logs)
resource "aws_iam_role_policy" "lambda_policy" {
  role = aws_iam_role.lambda_exec_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.report_storage.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = "${aws_sns_topic.support_alerts.arn}"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}