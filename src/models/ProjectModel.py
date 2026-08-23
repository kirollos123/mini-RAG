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
      return project(** record)
   async def get_all_projects(self ,page: int=1 , page_size :int=10):

   #count totla number of documnets 
    total_documnets = await self.collection.count_documnets({})
    total_page = total_documnets // page_size
    if total_documnets % page_size >0:
       total_pages +=1
   #collect  data 
    cursor =self.collection.find().skip((page-1)*page_size).limit(page_size)
    # curser 
    projects =[]
    async for documnets in cursor:
       projects.append(
           project(**documnets)
       )
       return projects,total_pages
 
    


