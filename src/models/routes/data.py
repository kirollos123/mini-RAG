# cleaned imports

from .schemes.data import ProcessRequest

from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse

import aiofiles
import logging
import os
from src.helpers.config import get_settings, Settings
from src.controllers import DataController
from src.controllers import projectController
from src.controllers import processController
from src.models.ProjectModel import ProjectModel
from src.models.ChunkModel import ChunkModel
from src.models.enums.ResponseEnums import ResponseSignal
from src.models.db_schemes import DataChunk, Asset
from src.models.AssetModel import AssetModel
from src.models.enums.AssetTypeEnum import AssetTypeEnum

logger = logging.getLogger("uvicorn.error")


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
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    data_controller = DataController()

    is_valid, signal = data_controller.validate_uploaded_file(
        file=file
    )

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": signal}
        )

    projectController().get_project_path(
        project_id=project_id
    )

    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id,
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(
                app_settings.FILE_DEFAULT_CHUNK_SIZE
            ):
                await f.write(chunk)

    except Exception as e:
        logger.error(f"Error while uploading file: {e}")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value
            }
        )
# store the assets into database
    asset_model = await AssetModel.create_instance(
        db_client=request.app.db_client
    )
    asset_resource= Asset(
        asset_project_id=project.id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path)
    )
    asset_record= await asset_model.create_asset(asset=asset_resource)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.FILE_UPLOADED.value,
            "file_id": str(asset_record.id),
            "project_id": str(project.id),
        }
    )


@data_router.post("/process/{project_id}")
async def process_endpoint(
    request: Request,
    project_id: str,
    process_request: ProcessRequest,
):
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    process_controller = processController(
        project_id=project_id
    )

    file_content = process_controller.get_file_content(
        file_id=file_id
    )

    file_chunks = process_controller.process_file_content(
        file_content=file_content,
        file_id=file_id,
        chunk_size=chunk_size,
        overlap_size=overlap_size,
    )

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROCESSING_FAILED.value
            }
        )
    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
    )

    if do_reset == 1:
        _ = await chunk_model.delete_chunks_by_project_id(
            project_id=project.id
        )

    file_chunks_records = [
        DataChunk(
            chunk_text=chunk.page_content,
            chunk_metadata=chunk.metadata,
            chunk_order=i + 1,
            chunk_project_id=project.id,
        )
        for i, chunk in enumerate(file_chunks)
    ]

    no_records = await chunk_model.insert_many_chunks(
        chunks=file_chunks_records
    )

    return {
        "signal": ResponseSignal.PROCESSING_SUCCES.value,
        "records": no_records,
    }
