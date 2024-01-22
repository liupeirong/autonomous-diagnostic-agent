import os
from dotenv import load_dotenv

load_dotenv("../.env")

class LLMConfig(object):
  _instance = None
  chat={}
  embedding={}
  vector_db={}
  search={}
  temperature=0
  max_tokens=300
  aoai={}

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super(LLMConfig, cls).__new__(cls)
      cls._instance.init()
    return cls._instance


  def init(self):
    self.aoai = {
      'endpoint': os.getenv("AZURE_OPENAI_ENDPOINT"),
      'api_key': os.getenv("AZURE_OPENAI_API_KEY"),
    }
    self.chat = {
      'deployment': os.getenv("AZURE_GPT35_DEPLOYMENT_NAME"),
      'api_version': os.getenv("AZURE_OPENAI_CHAT_API_VERSION"),
    }
    self.embedding = {
      'deployment': os.getenv("AZURE_EMBEDDINGS_DEPLOYMENT_NAME"),
      'api_version': os.getenv("AZURE_OPENAI_EMBEDDINGS_API_VERSION"),
    }
    self.vector_db = {
      'persistent_dir': os.getenv("CHROMA_DB_DIR"),
      'db_name': os.getenv("CHROMA_DB_NAME"),
    }
    self.search = {
      'endpoint': os.getenv("AZURE_SEARCH_ENDPOINT"),
      'index_name': os.getenv("AZURE_SEARCH_INDEX_NAME"),
      'api_key': os.getenv("AZURE_SEARCH_API_KEY"),
    }
    self.promptflow = {
      'aoai_connection_name': os.getenv("PROMPTFLOW_AOAI_CONNECTION_NAME"),
    }


class RobotConfig(object):
  _instance = None
  kinds=[]
  url_max_depth=1
  headers_to_split_on = [
    ("h1", "h1"),
    ("h2", "h2"),
    ("h3", "h3"),
    ("h4", "h4"),
    ("h5", "h5"),
  ]
  manuals_storage={}
  registration_file: str = None
  maintenace_dir: str = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super(RobotConfig, cls).__new__(cls)
      cls._instance.init()
    return cls._instance


  def init(self):
    self.url_max_depth = int(os.getenv("URL_MAX_DEPTH"))
    robots = os.getenv("ROBOTS").split(";")
    for robot in robots:
      name = robot.strip()
      manuals = os.getenv(f"ROBOT_MANUALS_{name.upper()}").split(";")
      self.kinds.append({
        "name": name,
        "manuals": manuals,
        "api_spec": f"./data/maintenance/{name.lower()}_openapi_spec.yaml"
      })
    self.manuals_storage = {
      "account": os.getenv("ADLS_MANUALS_ACCOUNT_URL"),
      "container": os.getenv("ADLS_MANUALS_CONTAINER_NAME"),
      "sas_token": os.getenv("ADLS_MANUALS_SAS_TOKEN"),
    }
    self.registration_file = os.getenv("ROBOTS_REGISTRATION_FILE")
    self.maintenance_dir = os.getenv("ROBOTS_MAINTENANCE_DIR")


class SQLConfig(object):
  _instance = None
  cxnstr = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super(SQLConfig, cls).__new__(cls)
      cls._instance.init()
    return cls._instance


  def init(self):
    server = os.getenv("AZURE_SQL_SERVER")
    db = os.getenv("AZURE_SQL_DB")
    user = os.getenv("AZURE_SQL_USER")
    password = os.getenv("AZURE_SQL_PASSWORD")
    driver = os.getenv("AZURE_SQL_DRIVER")

    self.cxnstr = f"DRIVER={driver};SERVER={server};DATABASE={db};UID={user};PWD={password}"


class CosmosConfig(object):
  _instance = None
  endpoint = None
  key = None
  database = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super(CosmosConfig, cls).__new__(cls)
      cls._instance.init()
    return cls._instance


  def init(self):
    self.endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
    self.key = os.getenv("AZURE_COSMOS_KEY")
    self.database = os.getenv("AZURE_COSMOS_DB")
