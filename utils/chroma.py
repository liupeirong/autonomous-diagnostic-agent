import chromadb
from loadenv import LLMConfig

class ChromaDBClient:
  db_client = None

  def __init__(self):
    config = LLMConfig()
    persistent_dir = config.vector_db["persistent_dir"]
    self.db_client = chromadb.PersistentClient(persistent_dir)

  
  def create_db(self, index_name):
    try: 
      self.db_client.get_collection(index_name)
      self.db_client.delete_collection(index_name)
    except ValueError:
      pass
    return self.db_client.create_collection(index_name)

  
  def get_db(self, index_name):
    return self.db_client.get_collection(index_name)