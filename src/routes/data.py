# cleaned imports

from .schemes.data import ProcessRequest
from fastapi import FastAPI, APIRouter, Depends, UploadFile, status,Request
from fastapi.responses import JSONResponse
import os
from src.helpers.config import get_settings, Settings
from src.controllers import DataController
from src.controllers import projectController
from src.controllers import processController
from src.models.ProjectModel import ProjectModel
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
    request: Request,
    project_id: str,
    file: UploadFile,
    app_settings: Settings = Depends(get_settings),
):
    project_model = ProjectModel(
        db_client=request.app.db_client
    )
    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )
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
        "file_id": file_id,
        "project_id": str(project.id)
    }
)

@data_router.post("/process/{project_id}")
async def process_endpoint(project_id: str, Process_Request: ProcessRequest):
     file_id = Process_Request.file_id
     chunk_size = Process_Request.chunk_size
     overlap_size = Process_Request.overlap_size

     process_controller = processController(project_id=project_id)
     file_content = process_controller.get_file_content(file_id=file_id)
     file_chunks=process_controller.process_file_content(
         file_content=file_content,
         file_id=file_id,
         chunk_size=chunk_size,
         overlap_size=overlap_size
         
     )
     if  file_chunks is None or len(file_chunks)==0:
         return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"signal": ResponseSignal.PROCESSING_FAILED.value}
                        )
     return file_chunks
         
