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
