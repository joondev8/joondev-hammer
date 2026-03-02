from .generator import create_price_report_by_av
from .uploader import upload_to_s3
import os

def lambda_handler(event, context):
    bucket = os.environ['S3_BUCKET_NAME']
    
    # Generate the file content
    file_content, file_name = create_price_report_by_av()
    
    # Upload it
    upload_to_s3(bucket, file_name, file_content)
    
    return {"status": "success"}