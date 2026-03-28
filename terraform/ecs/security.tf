resource "aws_security_group" "api_sg" {
  name        = "hammer-api-sg"
  description = "Security group for ECS Fargate API task"
  vpc_id      = data.terraform_remote_state.vpc.outputs.vpc_id

  # Inbound (Ingress) - Only if your container needs to accept traffic (e.g., API endpoint)
  # ingress {
  #   from_port   = 8000
  #   to_port     = 8000
  #   protocol    = "tcp"
  #   cidr_blocks = ["0.0.0.0/0"] # For a lead: restricted to your VPN or IP is better
  # }

  # Outbound (Egress) - REQUIRED to pull images and send logs
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "hammer-api-sg"
    Environment = "dev"
  }
}