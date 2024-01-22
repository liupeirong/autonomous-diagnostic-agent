import sys
import csv
import pyodbc

sys.path.append('./utils')
from loadenv import SQLConfig, RobotConfig


def create_robots_table():
  sqlCxnStr = SQLConfig().cxnstr
  sqlCxn = pyodbc.connect(sqlCxnStr)
  sqlCxn.execute("DROP TABLE IF EXISTS robots")
  sqlCxn.execute("CREATE TABLE robots (name VARCHAR(128) primary key, kind VARCHAR(64), purchase_date DATE, serial_number VARCHAR(256), manufacturer VARCHAR(128))")
  sqlCxn.commit()
  return sqlCxn


# assuming robots file is in the format:
# name, kind, purchase_date, serial_number, manufacturer
def register_robots(sqlCxn):
  robotConfig = RobotConfig()
  robotFile = robotConfig.registration_file
  with open(robotFile) as csvFile:
    csvReader = csv.reader(csvFile, delimiter=',')
    header = next(csvReader)
    for row in csvReader:
      name = row[0]
      kind = row[1]
      purchase_date = row[2]
      serial_number = row[3]
      manufacturer = row[4]

      robotSql = f"INSERT INTO robots VALUES ('{name}', '{kind}', '{purchase_date}', '{serial_number}', '{manufacturer}')"
      sqlCxn.execute(robotSql)
      sqlCxn.commit() 
 

if __name__ == "__main__":
  sqlCxn = create_robots_table()
  register_robots(sqlCxn)
