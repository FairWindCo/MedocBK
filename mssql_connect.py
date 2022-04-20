import clr

clr.AddReference("IronPython")
clr.AddReference("StdLib")
clr.AddReference("System.Data")
from System.Data import *
import json
import os

if os.path.exists('db.json'):
    json_data = open('db.json').read()
    config = json.loads(json_data)
else:
    config = {}

SERVER = config.get('server', '10.241.24.40:1433')
DB = config.get('db', 'RDCB')
DB_USER = config.get('user', None)
DB_PASS = config.get('pass', None)
CONN_URL = config.get('connect_url',
                      'SERVER=10.241.24.40,1433;Trusted_Connection=Yes;APP=Remote Desktop Services Connection Broker;DATABASE=RDCB;Connection Timeout=60;')

connection_params = []

if SERVER:
    connection_params.append('server=' + SERVER)
if DB:
    connection_params.append('database=' + DB)
if DB_USER:
    connection_params.append('uid=' + DB_USER)
if DB_PASS:
    connection_params.append('password=' + DB_PASS)

connection_str = CONN_URL if CONN_URL else ';'.join(connection_params)
print connection_str
# Connection string
conn = SqlClient.SqlConnection(connection_str)
try:
    conn.Open()
    try:
        cmd = SqlClient.SqlCommand('SELECT name FROM master.dbo.sysdatabases', conn)
        reader = cmd.ExecuteReader()
        if reader.HasRows:
            while reader.Read():
                print reader.GetString(reader.GetOrdinal('name'))
    finally:
        conn.Close()
except Exception as e:
    print "Connection Error", e
