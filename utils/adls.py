from typing import List
from datetime import datetime
from urllib.parse import urlparse
from langchain_core.documents.base import Document
from azure.storage.filedatalake import (
  DataLakeServiceClient,
  FileSystemClient
)
from loadenv import RobotConfig

class ADLSDocStore:
  fs_client: FileSystemClient

  def __init__(self):
    config = RobotConfig()
    account_url = config.manuals_storage["account"]
    sas_token = config.manuals_storage["sas_token"]
    container_name = config.manuals_storage["container"]
    service_client = DataLakeServiceClient(account_url, credential=sas_token)
    self.fs_client = service_client.get_file_system_client(file_system=container_name)
    if not self.fs_client.exists():
      self.fs_client.create_file_system()

  def store_docs(self, path, ext, docs: List[Document]):
    dir_client = self.fs_client.get_directory_client(path)
    if not dir_client.exists():
      dir_client.create_directory()
    
    for doc in docs:
      url_last_part = urlparse(doc.metadata['source']).path.split('/')[-1]
      time_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:-3]
      file_name = f"{url_last_part}_{time_str}.{ext}"
      file_client = dir_client.create_file(file_name)
      file_client.upload_data(doc.page_content, length=len(doc.page_content), overwrite=True)
      file_client.set_metadata(doc.metadata)
      file_client.close()


  def clear_path(self, path):
    dir_client = self.fs_client.get_directory_client(path)
    if dir_client.exists():
      dir_client.delete_directory()

  
  def get_docs(self, path, ext):
    docs = self.fs_client.get_paths(path=path)
    files = []
    for doc in docs:
      if not doc.is_directory and doc.name.endswith(ext):
        files.append(doc)
    return files

  
  def get_file(self, fullpath):
    file_client = self.fs_client.get_file_client(fullpath)
    file_contents = file_client.download_file()
    content_str = file_contents.readall().decode('utf-8')
    return content_str, file_client.get_file_properties().metadata
