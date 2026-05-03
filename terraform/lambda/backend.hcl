# backend.hcl
bucket         = "joondev-tfstate-925369342450"
region         = "us-east-1"
encrypt        = true
use_lockfile   = true
key            = "hammer/dev/lambda/terraform.tfstate"