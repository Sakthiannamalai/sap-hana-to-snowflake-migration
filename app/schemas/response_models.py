from pydantic import BaseModel


class ConvertFileRequest(BaseModel):
    file_uuid: str
    s3_link: str


class StatusResponse(BaseModel):
    status: str
    percentage: str


class FileConversionResponse(BaseModel):
    status: str
    message: str
    file_uuid: str
