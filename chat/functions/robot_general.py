import sys
import pyodbc
import json
from openai import AzureOpenAI
from azure.search.documents.models import VectorizedQuery, QueryType, QueryCaptionType, QueryAnswerType

sys.path.append('./utils')
from loadenv import SQLConfig, LLMConfig
from aaisearch import AAISearch


def get_robots(name: str = None, kind: str = None) -> str:
  sql = "SELECT * FROM robots"
  if name and kind:
    sql += f" WHERE name = '{name}' AND kind = '{kind}'"
  elif name:
    sql += f" WHERE name = '{name}'"
  elif kind:
    sql += f" WHERE kind = '{kind}'"
  sql += " FOR JSON PATH, ROOT('robots')"

  try:
    sqlCxnStr = SQLConfig().cxnstr
    sqlCxn = pyodbc.connect(sqlCxnStr)
    with sqlCxn:
      cursor = sqlCxn.cursor()
      cursor.execute(sql)
      result = cursor.fetchall()
      if len(result) == 0:
        return "not found."
      else:
        return result[0][0]
  except Exception as e:
    return "Failed to get robot info. Probably because database is not available. Please try again later."
  

def search_robot_manuals(query: str, kind: str = None) -> str:
  llmConfig = LLMConfig()
  aoai = AzureOpenAI(
    api_version=llmConfig.embedding['api_version']
  )
  aoaiDeployment = llmConfig.embedding['deployment']
  indexName = llmConfig.search['index_name']
  searchClient = AAISearch().get_search_client(indexName)

  queryEmbedding = aoai.embeddings.create(input=[query], model=aoaiDeployment).data[0].embedding
  vectorQuery = VectorizedQuery(vector=queryEmbedding, k_nearest_neighbors=3, fields="contentVector")
  results = searchClient.search(
    search_text=query,
    vector_queries=[vectorQuery],
    query_type=QueryType.SEMANTIC,
    semantic_configuration_name="default",
    query_caption=QueryCaptionType.EXTRACTIVE,
    query_answer=QueryAnswerType.EXTRACTIVE,
    top=3,
    filter=f"kind eq '{kind}'" if kind else None
  )

  docs = [{'title': result['title'], 'content': result['content']} for result in results]
  return json.dumps(docs)