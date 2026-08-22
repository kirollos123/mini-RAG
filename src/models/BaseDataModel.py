from helpers import get_settings , settings
class BaseDateModel:
  def __init__ (self,db_clint:object):
    self.db_clint = db_clint
    self.app_settings = get_settings
