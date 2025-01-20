import io
import json
import os
import zipfile

import boto3
import httpx
from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.config import (
    WEBAPP_USERNAME,
    WEBAPP_PASSWORD,
    WEBAPP_REMEMBERME,
    WEBAPP_AUTH_URL,
    WEBAPP_URL,
    AWS_ACCESS_KEY_ID,
    S3_REGION,
    AWS_SECRET_ACCESS_KEY,
    S3_BUCKET_NAME,
    S3_BUCKET_PATH,
    redis_client,
)
from app.status_manager import update_status
from app.schemas import ConvertFileRequest, StatusResponse
from app.services import (
    convert_function_to_snowflake,
    convert_schema_to_snowflake,
    convert_view_into_snowflake,
)
from app.schemas.response_models import FileConversionResponse
from app.utils import logger


router = APIRouter()


async def process_sap_hana_file(request: ConvertFileRequest):
    """
    This function will handle the file conversion in the background.
    """
    try:
        logger.info("Starting file conversion process.")
        update_status(request.file_uuid, "Started", '0%')

        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=S3_REGION
        )
        logger.info("S3 client initialized.")
        local_file_path = r"./saphanafiles"

        os.makedirs(local_file_path, exist_ok=True)

        if request.s3_link.startswith("s3://"):
            s3_parts = request.s3_link[5:].split("/", 1)
            bucket_name = s3_parts[0]
            s3_key = s3_parts[1]
            logger.info(f"Extracted bucket: {bucket_name}, key: {s3_key}")
        else:
            raise ValueError(
                "Invalid S3 URL format, expected 's3://<bucket>/<key>'")

        file_name = os.path.basename(s3_key)
        local_file_path = os.path.join(local_file_path, file_name)

        try:
            s3_client.download_file(bucket_name, s3_key, local_file_path)
            logger.info(f"File downloaded successfully: {local_file_path}")
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise

        if not os.path.exists(local_file_path):
            logger.error(f"ZIP file not found: {local_file_path}")
            raise FileNotFoundError(f"ZIP file not found: {local_file_path}")
        else:
            logger.info(f"Opening ZIP file: {local_file_path}")

        converted_files = []
        with zipfile.ZipFile(local_file_path, "r") as zip_ref:
            file_list = [f for f in zip_ref.infolist() if not f.is_dir()]
            total_files = len(file_list)

            for idx, zip_info in enumerate(file_list, start=1):
                logger.info(f"Processing file: {zip_info.filename}")
                file_content = zip_ref.read(zip_info.filename)
                file_extension = zip_info.filename.rsplit('.', 1)[-1].lower()

                if file_extension == "calculationview" or file_extension == "xml":
                    converted_content = await convert_view_into_snowflake(file_content)
                elif file_extension == "hdbdd":
                    converted_content = await convert_schema_to_snowflake(file_content)
                elif file_extension == "hdbscalarfunction":
                    converted_content = await convert_function_to_snowflake(file_content)
                else:
                    logger.warning(f"Unknown file extension '{
                                   file_extension}', skipping.")
                    continue

                converted_files.append((zip_info.filename.rsplit('.', 1)[
                                       0] + ".sql", converted_content))
                update_status(request.file_uuid, 'In Progress',
                              f"{int((idx / total_files) * 100)}%")

        if not converted_files:
            logger.error("No valid files to convert.")
            raise HTTPException(
                status_code=400, detail="No valid files to convert.")

        logger.info("All files processed and converted.")

        zip_output = io.BytesIO()
        with zipfile.ZipFile(zip_output, "w") as zip_ref:
            for filename, content in converted_files:
                if content is not None:
                    zip_ref.writestr(filename, content)
            else:
                logger.error(f"Content for {filename} is None, skipping file.")

        zip_output.seek(0)
        logger.info("ZIP archive with converted files is ready.")

        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=S3_BUCKET_PATH)
        logger.info(f"Folder '{S3_BUCKET_PATH}' created in bucket '{
                    S3_BUCKET_NAME}'.")

        converted_zip_key = f"{S3_BUCKET_PATH}{
            request.file_uuid}.zip"
        s3_client.upload_fileobj(
            zip_output, S3_BUCKET_NAME, converted_zip_key)
        logger.info("Successfully uploaded the converted ZIP file to S3.")

        s3_uri = f"s3://{S3_BUCKET_NAME}/{converted_zip_key}"

        logger.info(f"Generated S3 URI: {s3_uri}")

        auth_payload = {
            "username": WEBAPP_USERNAME,
            "password": WEBAPP_PASSWORD,
            "rememberMe": WEBAPP_REMEMBERME
        }

        async with httpx.AsyncClient() as client:
            auth_response = await client.post(WEBAPP_AUTH_URL, json=auth_payload)
            auth_response.raise_for_status()
            access_token = auth_response.json().get("id_token")

            if not access_token:
                logger.error("Authentication failed: No access token received")
                raise ValueError(
                    "Authentication failed: No access token received")

            logger.info("Authentication successful, access token obtained.")

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "file_uuid": request.file_uuid,
                "s3_link": s3_uri
            }

            webhook_response = await client.post(WEBAPP_URL, json=payload, headers=headers)
            webhook_response.raise_for_status()

            logger.info("Webhook response: %s, %s",
                        webhook_response.status_code, webhook_response.text)

            update_status(request.file_uuid, "Completed", "100%")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        update_status(request.file_uuid, "Failed", "")
        raise HTTPException(
            status_code=500, detail="An internal error occurred.")


@router.post("/sap-hana-to-snowflake", response_model=FileConversionResponse)
async def convert_sap_hana_file(request: ConvertFileRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to accept file conversion request and trigger background processing.
    """
    background_tasks.add_task(process_sap_hana_file, request)
    return FileConversionResponse(status="Accepted", message="File conversion process started.", file_uuid=request.file_uuid)


@router.get("/status/{file_uuid}", response_model=StatusResponse)
async def get_status(file_uuid: str):
    try:
        logger.info(f"Fetching status for file_uuid: {file_uuid}")

        status_data = redis_client.get(file_uuid)

        if status_data is None:
            logger.warning(f"No status found for file_uuid: {file_uuid}")
            raise HTTPException(
                status_code=404, detail=f"No status found for file_uuid: {file_uuid}")

        status_data = json.loads(status_data)

        if not status_data:
            logger.error(f"Invalid status data for file_uuid: {file_uuid}")
            raise HTTPException(status_code=400, detail="Invalid status data")

        status = status_data.get("status")
        percentage = status_data.get("percentage")

        logger.info(f"Status fetched successfully for file_uuid: {
                    file_uuid}, Status: {status}")

        return StatusResponse(status=status, percentage=percentage)

    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error for file_uuid: {
                     file_uuid}, Details: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to decode status data")

    except Exception as e:
        logger.error(f"An error occurred while fetching the status for file_uuid: {
                     file_uuid}, Details: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching the status")
