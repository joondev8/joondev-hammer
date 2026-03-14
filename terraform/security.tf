# Get the Prefix List ID for S3 in your region
# data "aws_prefix_list" "s3" {
#   prefix_list_id = aws_vpc_endpoint.s3.prefix_list_id
# }

# 1. Create a dedicated Security Group for the Ticker Loader Lambda
# resource "aws_security_group" "ticker_loader_lambda_sg" {
#   count       = local.ticker_loader_vpc_enabled ? 1 : 0
#   name_prefix = "ticker-loader-lambda-"
#   description = "Dedicated identity for joondev-hammer Lambda"
#   vpc_id      = var.lambda_vpc_id

#   # Allow outbound HTTPS to the S3 Prefix List only
#   egress {
#     from_port       = 443
#     to_port         = 443
#     protocol        = "tcp"
#     prefix_list_ids = [data.aws_prefix_list.s3.prefix_list_id]
#   }

#   tags = {
#     Name    = "ticker_loader_lambda_sg"
#     Project = "joondev-hammer"
#   }
# }

# 2. INBOUND: Allow the RDS (Citadel) to receive traffic from the Lambda
# resource "aws_security_group_rule" "db_ingress_from_lambda" {
#   count = local.ticker_loader_vpc_enabled && var.db_security_group_id != "" ? 1 : 0

#   type                     = "ingress"
#   from_port                = 5432
#   to_port                  = 5432
#   protocol                 = "tcp"
#   security_group_id        = var.db_security_group_id                         # Targeted SG (RDS)
#   source_security_group_id = aws_security_group.ticker_loader_lambda_sg[0].id # Source Identity
#   description              = "Allow ticker_loader Lambda to connect to PostgreSQL"
# }

# 3. OUTBOUND: Allow the Lambda to send traffic to the RDS
# resource "aws_security_group_rule" "lambda_egress_to_db" {
#   count = local.ticker_loader_vpc_enabled && var.db_security_group_id != "" ? 1 : 0

#   type                     = "egress"
#   from_port                = 5432
#   to_port                  = 5432
#   protocol                 = "tcp"
#   security_group_id        = aws_security_group.ticker_loader_lambda_sg[0].id # Current SG (Lambda)
#   source_security_group_id = var.db_security_group_id                         # Destination Identity
#   description              = "Allow Lambda to reach out to PostgreSQL"
# }