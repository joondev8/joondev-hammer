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

