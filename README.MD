# Joondev Hammer

A Python-based AWS Lambda function that generates CSV reports and uploads them to S3. This project automates the creation of transaction reports and stores them in cloud storage for archival and analysis.

## Overview

Joondev Hammer is a serverless application built with AWS Lambda that:
- Generates CSV transaction reports
- Uploads them to Amazon S3 for storage
- Can be scheduled using AWS EventBridge (configured via Terraform)
- Sends notifications on completion

## Project Structure

```
joondev-hammer/
├── src/
│   ├── generate_report.py      # Main Lambda handler
│   ├── jobs/
│   │   ├── generator.py        # CSV report generation
│   │   └── uploader.py         # S3 upload functionality
│   └── loaders/
├── terraform/
│   ├── main.tf                 # Infrastructure setup
│   ├── notifications.tf        # SNS notifications
│   └── scheduler.tf            # EventBridge scheduling
├── tests/
│   ├── test_generator.py
│   └── test_uploader.py
├── requirements.txt
└── pytest.ini
```

## Features

- **CSV Report Generation**: Creates timestamped transaction reports with transaction ID, date, amount, and currency
- **S3 Integration**: Uploads generated reports to AWS S3 buckets
- **Serverless Architecture**: Runs on AWS Lambda with no server management
- **Infrastructure as Code**: Complete Terraform configuration for AWS resources
- **Event-Driven**: Integrates with AWS EventBridge for scheduled execution
- **Notifications**: SNS integration for completion alerts

## Requirements

- Python 3.8+
- AWS Account with S3 bucket configured
- Terraform (for infrastructure deployment)

## Dependencies

See [requirements.txt](requirements.txt) for the complete list. Key dependencies:

- **boto3**: AWS SDK for Python (S3 and SNS integration)
- **python-dotenv**: Environment variable management
- **pytest**: Testing framework
- **moto**: Mock AWS services for testing

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd joondev-hammer
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your AWS configuration
export S3_BUCKET_NAME=your-bucket-name
```

## Usage

### Local Testing

Run the test suite:
```bash
pytest
```

Run tests with verbose output:
```bash
pytest -v
```

### AWS Deployment

Deploy infrastructure with Terraform:
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Triggering the Lambda

The Lambda function can be triggered:
- **Manually**: Via AWS Console or CLI
- **Scheduled**: Via EventBridge (see `scheduler.tf`)
- **Programmatically**: Via AWS SDK

## Environment Variables

- `S3_BUCKET_NAME`: The S3 bucket where reports will be uploaded

## Function Details

### `lambda_handler(event, context)`
Main Lambda entry point. Orchestrates the report generation and upload process.

**Returns**: `{"status": "success"}` on successful completion

### `create_price_report()`
Generates a CSV report with transaction data.

**Returns**: Tuple of (csv_content, filename)

### `upload_to_s3(bucket, filename, content)`
Uploads the CSV report to the specified S3 bucket.

## Testing

Tests use `moto` to mock AWS S3 services, allowing for safe local testing without AWS credentials:

```bash
pytest tests/
```

## Infrastructure

The Terraform configuration sets up:
- S3 bucket for report storage
- Lambda function with appropriate IAM roles
- EventBridge rule for scheduled execution
- SNS topics for notifications

## Contributing

1. Write tests for new features
2. Ensure all tests pass: `pytest`
3. Follow PEP 8 style guidelines
4. Update this README with any changes

## License

[Add your license information here]

## Support

For issues or questions, please open an issue in the repository.
