from .BaseDataModel import BaseDataModel
from .enums.DatabaseEnum import DatabaseEnum


class ChunkModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DatabaseEnum.COLLECTION_CHUNK_NAME.value]

    async def create_chunk(self, chunk: DataChunk):
        result = await self.collection.insert_one(chunk.dict())
        chunk._id = result.insert_id
        return chunk
    
