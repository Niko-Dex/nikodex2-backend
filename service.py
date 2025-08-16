import sqlite3
from models import niko_convert

import mysql.connector

session = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="twm",
    password="$nikodev0Dex!?")

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
