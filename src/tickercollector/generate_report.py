from tickercollector.generator import create_price_report_by_av
from tickercollector.uploader import upload_to_s3
import logging
import os


# def lambda_handler(event, context):
#     bucket = os.environ['S3_BUCKET_NAME']

#     # Generate the file content
#     file_content, file_name = create_price_report_by_av()

#     # Upload it
#     upload_to_s3(bucket, file_name, file_content)

#     return {"status": "success"}

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    
    bucket = os.environ['S3_BUCKET_NAME']

    logger.info("Starting report generation for bucket: %s", bucket)
    file_content, file_name = create_price_report_by_av()
    
    logger.info("Report generated: %s", file_name)
    upload_to_s3(bucket, file_name, file_content)
    logger.info("Report upload complete")

if __name__ == "__main__":
    main()
