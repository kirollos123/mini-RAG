from .BaseController import BaseController
from .projectController import projectController
import os
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from models import processingEnum

class processController(BaseController):
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.project_path = projectController().get_project_path(project_id=project_id)

    def get_file_extenstion(self, file_id: str):
        return os.path.splitext(file_id)(-1)

    def get_file_loader(self, file_id: str):
        file_ext = self.get_file_extenstion(file_id=file_id)
        file_path=os.path.join(
            self.project_path,
            file_id
        )
        if file_ext == processingEnum.TXT.value:
            return TextLoader(file_path,encding="utf-8")
        if file_ext == processingEnum.PDF.value:

          return PyMuPDFLoader(file_path)
        return None
    def get_file_content(self,file_id:str):
        loader = self.get_file_loader(file_id=file_id)
        return loader.load()