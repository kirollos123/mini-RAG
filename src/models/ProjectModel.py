from .BaseDateModel import BaseDateModel
from .db_schemes import project
from .enums.DatabaseEnum import databasenum

class projectModel(BaseDateModel):
   def __init__ (self,db_clint:object):
      super().__init__(db_client=db_clint)
      self.collection = self.db_clint[DatabaseEnum.COLLECTION_PROJECT_NAME.value]


   async def create_project(self, project: project):

      result =await self.collection.insert_one(project.dict())
      project._id = result.inserted_id
      return project

   async def get_project_or_create_one(self, project_id:str):
      record =await self.collection.find_one({
          "project_id": project_id
      })
      if record is None:
         # create new project
         project = project(project_id=project_id)
         project = await self.create_project(project=project)
         return project
      return project(**record)


