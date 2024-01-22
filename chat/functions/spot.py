import sys
import pyodbc
from flask import Flask

sys.path.append('utils')
from loadenv import SQLConfig

app = Flask(__name__)

@app.route('/maintenance/<name>')
def get_maintenance(name: str):
  tableName = "maintenance_spot"
  sql = f"SELECT robot as name, date, description, next_maintenance_date, remarks FROM {tableName} WHERE robot = '{name}' FOR JSON PATH, ROOT('maintenance')"

  try:
    sqlCxnStr = SQLConfig().cxnstr
    sqlCxn = pyodbc.connect(sqlCxnStr)
    with sqlCxn:
      cursor = sqlCxn.cursor()
      cursor.execute(sql)
      result = cursor.fetchall()
      if len(result) == 0:
        return '{"error": "No maintenance records found."}'
      else:
        return result[0][0]
  except Exception as e:
    return '{"error": "Failed to get maintenance info. Probably because database is not available. Please try again later."}'

if __name__ == '__main__':
  result = get_maintenance("spot_jr")
  print(result)