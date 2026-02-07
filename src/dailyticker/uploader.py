import boto3
import logging

# Set up logging so you can see what's happening in CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def upload_to_s3(bucket_name, file_name, content):
    """
    Uploads a string content to a specific S3 bucket
    """
    s3 = boto3.client('s3')
    
    try:
        logger.info(f"Attempting to upload {file_name} to {bucket_name}")
        
        s3.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=content
        )
        
        logger.info("Upload successful.")
        return True
        
    except Exception as e:
        logger.error(f"Failed to upload to S3: {str(e)}")
        # We re-raise the error so the Lambda fails and triggers the SNS alert
        raise e