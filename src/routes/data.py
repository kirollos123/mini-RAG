# cleaned imports

from fastapi import FastAPI, APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
import os
from src.helpers.config import get_settings, Settings
from src.controllers import DataController
from src.controllers import projectController
import aiofiles
import logging
logger = logging.getLogger('uvicron.error')
from src.models.enums.ResponseEnums import ResponseSignal

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)


@data_router.post("/upload/{project_id}")
async def upload_data(
    project_id: str,
    file: UploadFile,
    app_settings: Settings = Depends(get_settings),
):
    data_controller = DataController()
    is_valid, signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": signal}
        )

    project_dir_path = projectController().get_project_path(project_id=project_id)
    file_path ,file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id,
    )
    try:
        async with aiofiles.open(file_path, "wb") as f:
          while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
             await f.write(chunk)
    except Exception as e :
       logger.error(f"Eroor while uploading file : {e} " )
       return JSONResponse(
                   status_code=status.HTTP_400_BAD_REQUEST,
                   content={"signal": ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value}
               )
       
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.FILE_UPLOADED.value,
            "file_id": file_id
        }
    )
