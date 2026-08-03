from fastapi import FastAPI

from src.routes.base import base_router

app = FastAPI()
app.include_router(base_router)