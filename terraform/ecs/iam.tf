# The task role is for the permissions your containerized application needs to interact with AWS services (e.g., S3, DynamoDB)
resource "aws_iam_role" "hammer_task_role" {
  name = "hammer-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "hammer_task_s3_policy" {
  name = "hammer-task-s3-policy"
  role = aws_iam_role.hammer_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:ListBucket"
      ]
      Resource = [
        "arn:aws:s3:::${var.bucket_name}",
        "arn:aws:s3:::${var.bucket_name}/*"
      ]
    }]
  })
}

# The execution role stays because it's still needed for ECR and Logs
# It is to set up the container execution environment, allowing ECS to pull images and send logs to CloudWatch
resource "aws_iam_role" "hammer_exec_role" {
  name = "hammer-execution-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "hammer_exec_role_policy" {
  role       = aws_iam_role.hammer_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "hammer_eventbridge_role" {
  name = "hammer-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "hammer_eventbridge_policy" {
  name = "hammer-eventbridge-policy"
  role = aws_iam_role.hammer_eventbridge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ecs:RunTask"]
        Resource = [aws_ecs_task_definition.api.arn]
      },
      {
        Effect = "Allow"
        Action = ["iam:PassRole"]
        Resource = [
          aws_iam_role.hammer_task_role.arn,
          aws_iam_role.hammer_exec_role.arn
        ]
      }
    ]
  })
}

# IAM role for the collector ECS task (s3:PutObject only)
resource "aws_iam_role" "hammer_collector_task_role" {
  name = "hammer-collector-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "hammer_collector_task_s3_policy" {
  name = "hammer-collector-task-s3-policy"
  role = aws_iam_role.hammer_collector_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject"]
      Resource = "arn:aws:s3:::${var.bucket_name}/*"
    }]
  })
}

# IAM role for EventBridge Scheduler to trigger the collector ECS task
resource "aws_iam_role" "collector_scheduler_role" {
  name = "hammer-collector-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "collector_scheduler_policy" {
  name = "hammer-collector-scheduler-policy"
  role = aws_iam_role.collector_scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ecs:RunTask"]
        Resource = [aws_ecs_task_definition.collector.arn]
      },
      {
        Effect = "Allow"
        Action = ["iam:PassRole"]
        Resource = [
          aws_iam_role.hammer_collector_task_role.arn,
          aws_iam_role.hammer_exec_role.arn
        ]
      }
    ]
  })
}
