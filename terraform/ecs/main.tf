# AWS Provider Configuration
provider "aws" {
  region = "us-east-1"
  assume_role {
    # This is the role that Terraform will assume to create resources. Make sure it has the necessary permissions.
    role_arn     = var.terraform_execution_role_arn
    session_name = "TerraformSession"
  }
}

terraform {
  backend "s3" {}
}

# Fetch the vpc outputs (assumes local state for this example)
data "terraform_remote_state" "vpc" {
  backend = "s3"
  config = {
    bucket  = "joondev-tfstate-925369342450"
    key     = "citadel/dev/vpc/terraform.tfstate"
    region  = "us-east-1"
  }
}

# S3 Bucket for report storage (moved from lambda module)
resource "aws_s3_bucket" "report_storage" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_notification" "report_storage_eventbridge" {
  bucket      = aws_s3_bucket.report_storage.id
  eventbridge = true
}

resource "aws_ecr_repository" "hammer_api" {
  name                 = "hammer-api"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# CloudWatch Log Group for ECS task output
resource "aws_cloudwatch_log_group" "ecs_log_group" {
  name              = "/ecs/hammer-api"
  retention_in_days = 7 # Save money by not keeping dev logs forever

  tags = {
    Environment = "dev"
    Project     = "hammer"
  }
}

resource "aws_ecs_cluster" "main" {
  name = "hammer-cluster-dev"
}

# 3. Configure Capacity Providers for Fargate Spot
# resource "aws_ecs_cluster_capacity_providers" "main" {
#   cluster_name = data.terraform_remote_state.ecs.outputs.ecs_cluster_name

#   capacity_providers = ["FARGATE", "FARGATE_SPOT"]

#   default_capacity_provider_strategy {
#     capacity_provider = "FARGATE_SPOT"
#     weight            = 100
#   }
# }

# ECS Task Definition
resource "aws_ecs_task_definition" "api" {
  family                   = "hammer-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  task_role_arn            = aws_iam_role.hammer_task_role.arn
  execution_role_arn       = aws_iam_role.hammer_exec_role.arn # For pulling from ECR and logging

  container_definitions = jsonencode([{
    name      = "hammer-api"
    image     = "925369342450.dkr.ecr.us-east-1.amazonaws.com/hammer-api:${var.image_tag}"
    essential = true

    environment = [
      { name = "AWS_REGION", value = "us-east-1" },
      { name = "S3_BUCKET_NAME", value = var.bucket_name },
      { name = "DB_HOST", value = var.db_host },
      { name = "DB_PORT", value = tostring(var.db_port) },
      { name = "DB_NAME", value = var.db_name },
      { name = "DB_USERNAME", value = var.db_username },
      { name = "DB_PASSWORD", value = var.db_password },
      { name = "DB_SCHEMA", value = var.db_schema },
      { name = "DB_SSLMODE", value = var.db_sslmode }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/hammer-api"
        "awslogs-region"        = "us-east-1"
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# resource "aws_ecs_service" "api_service" {
#   name            = "hammer-api-service"
#   cluster         = data.terraform_remote_state.ecs.outputs.ecs_cluster_id
#   task_definition = aws_ecs_task_definition.api.arn
#   desired_count   = 1

#   capacity_provider_strategy {
#     capacity_provider = "FARGATE_SPOT"
#     weight            = 1
#   }

#   network_configuration {
#     subnets          = data.terraform_remote_state.vpc.outputs.public_subnets
#     assign_public_ip = true
#     security_groups  = [aws_security_group.api_sg.id]
#   }

#   depends_on = [aws_ecs_cluster_capacity_providers.main]
# }

resource "aws_cloudwatch_event_rule" "s3_object_created" {
  name        = "hammer-s3-object-created"
  description = "Triggers ECS task when a new file is uploaded to the report storage bucket"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = { name = [var.bucket_name] }
    }
  })
}

resource "aws_cloudwatch_event_target" "ecs_task" {
  rule     = aws_cloudwatch_event_rule.s3_object_created.name
  arn      = aws_ecs_cluster.main.arn
  role_arn = aws_iam_role.hammer_eventbridge_role.arn

  ecs_target {
    task_definition_arn = aws_ecs_task_definition.api.arn
    task_count          = 1
    launch_type         = "FARGATE"

    network_configuration {
      subnets          = data.terraform_remote_state.vpc.outputs.private_subnets
      assign_public_ip = true
      security_groups  = [aws_security_group.api_sg.id]
    }
  }

  input_transformer {
    input_paths = {
      bucket = "$.detail.bucket.name"
      key    = "$.detail.object.key"
    }
    input_template = <<-EOT
      {
        "containerOverrides": [{
          "name": "hammer-api",
          "environment": [
            {"name": "S3_BUCKET_NAME", "value": <bucket>},
            {"name": "S3_OBJECT_KEY", "value": <key>}
          ]
        }]
      }
    EOT
  }
}

# CloudWatch Log Group for the collector task
resource "aws_cloudwatch_log_group" "collector_log_group" {
  name              = "/ecs/hammer-collector"
  retention_in_days = 7

  tags = {
    Environment = "dev"
    Project     = "hammer"
  }
}

# ECS Task Definition for the scheduled report collector
resource "aws_ecs_task_definition" "collector" {
  family                   = "hammer-collector"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  task_role_arn            = aws_iam_role.hammer_collector_task_role.arn
  execution_role_arn       = aws_iam_role.hammer_exec_role.arn

  container_definitions = jsonencode([{
    name      = "hammer-collector"
    image     = "925369342450.dkr.ecr.us-east-1.amazonaws.com/hammer-api:${var.image_tag}"
    essential = true
    command   = ["python", "-m", "tickercollector.generate_report"]

    environment = [
      { name = "AWS_REGION", value = "us-east-1" },
      { name = "S3_BUCKET_NAME", value = var.bucket_name },
      { name = "AV_API_KEY", value = var.av_api_key }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/hammer-collector"
        "awslogs-region"        = "us-east-1"
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}