import sys
import json
from azure.cosmos import CosmosClient
from flask import Flask, Response

sys.path.append('utils')
from loadenv import CosmosConfig

app = Flask(__name__)

@app.route('/maintenance_records/<name>')
def get_maintenance_records(name: str):
  cosmosConfig = CosmosConfig()
  cosmosClient = CosmosClient(url=cosmosConfig.endpoint, credential=cosmosConfig.key)
  containerName = "maintenance_petoi"
  try: 
    cosmosDB = cosmosClient.get_database_client(cosmosConfig.database)
    container = cosmosDB.get_container_client(containerName)
    items = container.query_items(query=f"SELECT c.name, c.date, c.inspection_result, c.notes FROM c WHERE c.name = '{name}'", enable_cross_partition_query=True)
    response = Response(json.dumps(list(items)), status=200, mimetype='application/json')
  except:
    response = Response('"error": "Failed to get maintenance info."', status=500, mimetype='application/json')

  return response


if __name__ == '__main__':
  result = get_maintenance_records("petoi_dog")
  print(result)