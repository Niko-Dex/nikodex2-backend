import os
import mysql.connector

session = mysql.connector.connect(
    host=os.environ['MYSQL_URI'],
    port=os.environ['MYSQL_PORT'],
    user=os.environ['MYSQL_USER'],
    password=os.environ['MYSQL_PASS'])

cur = session.cursor()
cur.execute("USE nikodex;")

cur.execute("SELECT * FROM nikos;")

row = cur.fetchone()
print(row)