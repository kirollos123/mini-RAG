from .BaseController import BaseController
from fastapi import UploadFile


class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.size_scale = 1048576

    def validate_uploaded_file(self, file: UploadFile):
        print("Content-Type:", file.content_type)
        print("Size:", file.size)
        print("Allowed:", self.app_settings.FILE_ALLOWED_TYPES)
        print("Max Size:", self.app_settings.FILE_MAX_SIZE_MB)

        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            
            return False," Invalid content type"

        if file.size > self.app_settings.FILE_MAX_SIZE_MB * self.size_scale:
           
            return False , " File too large"

       
        return True," File is valid"
