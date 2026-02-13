resource "aws_scheduler_schedule" "weekday_report" {
  name = "generate-report-8pm-weekdays"

  flexible_time_window {
    mode = "OFF"
  }

  # cron(Minutes Hours Day-of-month Month Day-of-week Year)
  schedule_expression          = "cron(0 20 ? * MON-FRI *)"
  schedule_expression_timezone = "America/New_York" # Change to your timezone

  target {
    arn      = aws_lambda_function.report_gen.arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}

# IAM Role for Scheduler to trigger Lambda
resource "aws_iam_role" "scheduler_role" {
  name = "report_scheduler_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_invoke" {
  role = aws_iam_role.scheduler_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = aws_lambda_function.report_gen.arn
    }]
  })
}