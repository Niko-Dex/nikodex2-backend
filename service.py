import os
from dotenv import load_dotenv
from models import niko_convert
import mysql.connector

load_dotenv()

session = mysql.connector.connect(
    host=os.environ['MYSQL_URI'],
    port=os.environ['MYSQL_PORT'],
    user=os.environ['MYSQL_USER'],
    password=os.environ['MYSQL_PASS'])

cur = session.cursor()
cur.execute("USE nikodex;")

def get_all():
    cur.execute("SELECT * FROM nikos")
    result = cur.fetchall()
    lis = list()
    for res in result:
        lis.append(niko_convert(res))
    return lis

def get_by_name(name: str):
    cur.execute("SELECT * FROM nikos WHERE name LIKE %s", (name,))
    result = cur.fetchall()
    lis = list()
    for res in result:
        lis.append(niko_convert(res))
    return lis

def close_connection():
    cur.close()
    session.close()