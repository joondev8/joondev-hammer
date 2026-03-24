import boto3
import pytest
from moto import mock_aws
from unittest.mock import patch, MagicMock
from tickercollector.uploader import upload_to_s3

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


@patch('tickercollector.uploader.boto3.client')
def test_upload_to_s3_raises_on_failure(mock_boto_client):
    """Verify that upload_to_s3 re-raises exceptions from S3"""
    mock_s3 = MagicMock()
    mock_s3.put_object.side_effect = Exception("S3 service unavailable")
    mock_boto_client.return_value = mock_s3

    with pytest.raises(Exception, match="S3 service unavailable"):
        upload_to_s3("test-bucket", "test_file.csv", "content")
