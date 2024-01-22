import sys
import csv
import pyodbc
from azure.cosmos import CosmosClient, PartitionKey

sys.path.append('./utils')
from loadenv import SQLConfig, CosmosConfig, RobotConfig

# assuming:
#   1. we keep maintenance records for spot in SQL, and petoi in Cosmos
#   2. spot maintenance records are in the format:
#      robot|date|description|performed_by|date_validation|validated_by|next_maintenance_date|remarks
#   3. petoi maintenance records are in the format:
#      name|date|performed|performed_by|inspection_result|next_maintenance_date|notes

# create sql table for spot
def create_sql_maintenance_table(tableName):
  sqlCxnStr = SQLConfig().cxnstr
  sqlCxn = pyodbc.connect(sqlCxnStr)
  sqlCxn.execute(f"DROP TABLE IF EXISTS {tableName}")
  sqlCxn.execute(f"""
    CREATE TABLE {tableName} (robot VARCHAR(128) index IDX_robotName, date DATETIME, description VARCHAR(256), performed_by VARCHAR(64),
                 date_validation DATETIME, validated_by VARCHAR(65), next_maintenance_date DATE, remarks VARCHAR(256))
  """)
  sqlCxn.commit()
  return sqlCxn


# ingest maintenance records for spot to sql
def ingest_maintenance_records_to_sql(sqlCxn, tableName):
  robotConfig = RobotConfig()
  maintenanceFile = robotConfig.maintenance_dir + "/spot.csv"
  with open(maintenanceFile) as csvFile:
    csvReader = csv.reader(csvFile, delimiter='|')
    header = next(csvReader)
    for row in csvReader:
      robot = row[0]
      date = row[1]
      description = row[2].replace("'", "''")
      performed_by = row[3]
      date_validation = row[4]
      validated_by = row[5]
      next_maintenance_date = row[6]
      remarks = row[7].replace("'", "''")

      sql = f"INSERT INTO {tableName} VALUES ('{robot}', '{date}', '{description}', '{performed_by}', '{date_validation}', '{validated_by}', '{next_maintenance_date}', '{remarks}')"
      sqlCxn.execute(sql)
      sqlCxn.commit()


# create cosmos container for petoi
def create_cosmos_container(containerName):
  cosmosConfig = CosmosConfig()
  cosmosClient = CosmosClient(url=cosmosConfig.endpoint, credential=cosmosConfig.key)
  cosmosDB = cosmosClient.create_database_if_not_exists(cosmosConfig.database)
  try: 
    cosmosDB.delete_container(containerName)
  except:
    pass
  container = cosmosDB.create_container(id=containerName, partition_key=PartitionKey(path="/name"))
  return container


# ingest maintenance records for petoi to cosmos
def ingest_maintenance_records_to_cosmos(container):
  robotConfig = RobotConfig()
  maintenanceFile = robotConfig.maintenance_dir + "/petoi.csv"
  with open(maintenanceFile) as csvFile:
    csvReader = csv.reader(csvFile, delimiter='|')
    header = next(csvReader)
    for row in csvReader:
      name = row[0]
      date = row[1]
      performed = row[2]
      performed_by = row[3]
      inspection_result = row[4]
      next_maintenance_date = row[5]
      notes = row[6]

      item = {
        "name": name,
        "date": date,
        "performed": performed,
        "performed_by": performed_by,
        "inspection_result": inspection_result,
        "next_maintenance_date": next_maintenance_date,
        "notes": notes,
      }
      container.create_item(item, enable_automatic_id_generation=True)


if __name__ == '__main__':
  tableName = "maintenance_spot"
  sqlCxn = create_sql_maintenance_table(tableName)
  ingest_maintenance_records_to_sql(sqlCxn, tableName)

  containerName = "maintenance_petoi"
  container = create_cosmos_container(containerName)
  ingest_maintenance_records_to_cosmos(container)
