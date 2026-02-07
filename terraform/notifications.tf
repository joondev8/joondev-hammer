resource "aws_sns_topic" "support_alerts" {
  name = "report-failure-alerts"
}

resource "aws_sns_topic_subscription" "support_email" {
  topic_arn = aws_sns_topic.support_alerts.arn
  protocol  = "email"
  endpoint  = var.support_email
}

# Connect Lambda Failure to SNS
resource "aws_lambda_function_event_invoke_config" "failure_config" {
  function_name                = aws_lambda_function.report_gen.function_name
  maximum_retry_attempts       = 0
  
  destination_config {
    on_failure {
      destination = aws_sns_topic.support_alerts.arn
    }
  }
}