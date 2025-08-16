import mysql.connector

session = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="twm",
    password="$nikodev0Dex!?")

cur = session.cursor()
cur.execute("USE nikodex;")

cur.execute("SELECT * FROM nikos;")

row = cur.fetchone()
print(row)