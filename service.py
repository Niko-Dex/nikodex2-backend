import os
from dotenv import load_dotenv
from models import Niko, Ability
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, select

load_dotenv()

connection_str = "mysql+mysqlconnector://{}:{}@{}:{}/{}" \
    .format(os.environ['MYSQL_USER'], os.environ['MYSQL_PASS'], os.environ['MYSQL_URI'], os.environ['MYSQL_PORT'], "nikodex")

engine = create_engine(connection_str, echo=True)

session = Session(engine)

def get_all():
    stmt = select(Niko).join(Niko.abilities)
    result_list = list()
    for niko in session.scalars(stmt):
        result_list.append(niko)
        print(niko.abilities)
    return session.scalars(stmt).fetchall()

def get_by_name(name: str):
    stmt = select(Niko).join(Niko.abilities).where(Niko.name.like(name))
    result_list = list()
    for niko in session.scalars(stmt):
        result_list.append(niko)
        print(niko.abilities)
    return session.scalars(stmt).fetchall()

def get_abilities():
    stmt = select(Ability)
    return session.scalars(stmt).fetchall()

def get_ability_by_id(id: int):
    stmt = select(Ability).where(Ability.id == id)
    return session.scalars(stmt).one()

def close_connection():
    session.close()