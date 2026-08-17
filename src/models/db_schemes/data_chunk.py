from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import objectid


class datachnuk (BaseModel):
    _id: Optional[objectid]
    chunk_text: str = Field(..., min_lenght=1)
    chunk_metadata: dict
    chunk_order: int = Field(..., gt=0)
    chunk_project_id: objectid

    class config:
        arbitraty_types_allowed = True
