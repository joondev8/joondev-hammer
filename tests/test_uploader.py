import boto3
import pytest
from moto import mock_aws
from dailyticker.uploader import upload_to_s3

@mock_aws
def test_upload_to_s3_success():
    """Verify that the uploader successfully pushes a file to a mocked S3 bucket"""
    bucket_name = "test-bucket"
    file_name = "test_file.csv"
    content = "ID,Status\n1,Success"
    
    # Setup: We must create the bucket in the mock environment first
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=bucket_name)
    
    # Act: Run the real uploader function
    result = upload_to_s3(bucket_name, file_name, content)
    
    # Assert: Check if the file actually exists in our mock S3
    response = s3.get_object(Bucket=bucket_name, Key=file_name)
    uploaded_content = response['Body'].read().decode('utf-8')
    
    assert result is True
    assert uploaded_content == content
