from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# @app.get("/health")
# async def healthcheck():
#     """
#     Health check endpoint to verify service is running.
#     Returns service status and timestamp.
#     """
#     return {
#         "status": "healthy",
#         "service": "hammer-service",
#         "timestamp": datetime.now(UTC).isoformat(),
#         "version": "1.0.0"
#     }

# @app.post("/ticker-files/{filename}/load")
# async def load_ticker_file_from_s3(filename: str):
#     bucket = os.getenv("S3_BUCKET_NAME")
#     if not bucket:
#         raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured")

#     event = {
#         "Records": [{
#             "s3": {
#                 "bucket": {"name": bucket},
#                 "object": {"key": filename}
#             }
#         }]
#     }

#     try:
#         result = load_report_to_db(event, None)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#     if result.get("status") == "failed":
#         raise HTTPException(status_code=500, detail=result)

#     return result