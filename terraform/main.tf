# AWS Provider Configuration
provider "aws" {
  region = "us-east-1"
  assume_role {
    # This is the role that Terraform will assume to create resources. Make sure it has the necessary permissions.
    role_arn     = var.terraform_execution_role_arn
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

data "archive_file" "common_libs_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../python"
  output_path = "${path.module}/common_libs.zip"
}


resource "aws_lambda_layer_version" "python_dependencies" {
  filename            = "${path.module}/common_libs.zip"
  layer_name          = "python-dependencies"
  compatible_runtimes = ["python3.11"]
}

# Lambda Function
resource "aws_lambda_function" "report_gen" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "DailyTickerReportGenerator"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "dailyticker.generate_report.lambda_handler"
  runtime          = "python3.11"
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

resource "aws_lambda_function" "ticker_loader" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "TickerReportLoader"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "tickerloader.load_report.lambda_handler"
  runtime          = "python3.11"
  layers           = [aws_lambda_layer_version.python_dependencies.arn]
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 120
  memory_size      = 256

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.report_storage.id
      DB_HOST        = var.db_host
      DB_PORT        = var.db_port
      DB_NAME        = var.db_name
      DB_USERNAME    = var.db_username
      DB_PASSWORD    = var.db_password
      DB_SCHEMA      = var.db_schema
      DB_SSLMODE     = var.db_sslmode
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
        Action   = ["s3:PutObject", "s3:GetObject"]
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

resource "aws_lambda_permission" "allow_s3_invoke_ticker_loader" {
  statement_id  = "AllowExecutionFromS3ForTickerLoader"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ticker_loader.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.report_storage.arn
}

resource "aws_s3_bucket_notification" "ticker_loader_trigger" {
  bucket = aws_s3_bucket.report_storage.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.ticker_loader.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "stock_price_"
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke_ticker_loader]
}