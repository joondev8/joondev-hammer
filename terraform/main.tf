# AWS Provider Configuration
provider "aws" {
  region = "us-east-1"
  assume_role {
    # This is the role that Terraform will assume to create resources. Make sure it has the necessary permissions.
    role_arn     = var.terraform_execution_role_arn
    session_name = "TerraformSession"
  }
}

# Fetch the vpc outputs (assumes local state for this example)
data "terraform_remote_state" "vpc" {
  backend = "local"
  config  = { path = "../../joondev-oms-citadel/terraform/vpc/terraform.tfstate" }
}

# Create the S3 Bucket
resource "aws_s3_bucket" "report_storage" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_notification" "report_storage_eventbridge" {
  bucket      = aws_s3_bucket.report_storage.id
  eventbridge = true
}

# Automatically zip the source code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/lambda_function.zip"
}

data "archive_file" "hammer_common_libs_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-layer"
  output_path = "${path.module}/hammer_common_libs.zip"
}


resource "aws_lambda_layer_version" "python_dependencies" {
  filename            = "${path.module}/hammer_common_libs.zip"
  layer_name          = "python-dependencies"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = data.archive_file.hammer_common_libs_zip.output_base64sha256
}

# Lambda Function
resource "aws_lambda_function" "report_gen" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "hammer-price-report-downloader"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "tickercollector.generate_report.lambda_handler"
  runtime          = "python3.12"
  layers           = [aws_lambda_layer_version.python_dependencies.arn]
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 60  # Increased from the default (3s) to 60 seconds
  memory_size      = 256 # Consider bumping this if the reports are large

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.report_storage.id
      AV_API_KEY     = var.av_api_key
    }
  }
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.report_gen.function_name}"
  retention_in_days = 7
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "hammer-lambda-role"

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
resource "aws_iam_role_policy" "lambda_exec_policy" {
  role = aws_iam_role.lambda_exec_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "${aws_s3_bucket.report_storage.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}
