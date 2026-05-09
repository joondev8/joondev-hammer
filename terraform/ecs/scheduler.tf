resource "aws_scheduler_schedule" "weekday_collector" {
  name = "hammer-price-report-collector-8pm-weekdays"

  flexible_time_window {
    mode = "OFF"
  }

  # cron(Minutes Hours Day-of-month Month Day-of-week Year)
  schedule_expression          = "cron(0 20 ? * MON-FRI *)"
  schedule_expression_timezone = "America/New_York"

  target {
    arn      = aws_ecs_cluster.main.arn
    role_arn = aws_iam_role.collector_scheduler_role.arn

    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.collector.arn
      task_count          = 1
      launch_type         = "FARGATE"

      network_configuration {
        subnets          = data.terraform_remote_state.vpc.outputs.private_subnets
        assign_public_ip = true
        security_groups  = [aws_security_group.hammer_sg.id]
      }
    }
  }
}
