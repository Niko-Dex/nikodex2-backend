import os
from dotenv import load_dotenv
from models import Niko, Ability, User
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, create_engine, text, select, insert, func
import dto

load_dotenv()

connection_str = "mysql+mysqlconnector://{}:{}@{}:{}/{}" \
    .format(os.environ['MYSQL_USER'], os.environ['MYSQL_PASS'], os.environ['MYSQL_URI'], os.environ['MYSQL_PORT'], "nikodex")

engine = create_engine(connection_str, echo=True)

session = Session(engine)

def get_all():
    stmt = select(Niko).options(selectinload(Niko.abilities))
    return session.scalars(stmt).fetchall()

def get_by_name(name: str):
    stmt = select(Niko).options(selectinload(Niko.abilities)).where(Niko.name.like(name))
    return session.scalars(stmt).fetchall()

def get_niko_by_id(id: int):
    stmt = select(Niko).options(selectinload(Niko.abilities)).where(Niko.id == id)
    res = session.scalars(stmt).one()
    return res

def get_nikos_count():
    return session.query(func.count(Niko.id)).one()[0]

def insert_niko(req: dto.NikoRequest):
    stmt = insert(Niko).values(name=req.name, description=req.description,
        image=req.image, doc="", author=req.author, full_desc=req.full_desc)
    
    result = session.execute(stmt)
    session.commit()

def get_abilities():
    stmt = select(Ability)
    return session.scalars(stmt).fetchall()

def get_ability_by_id(id: int):
    stmt = select(Ability).where(Ability.id == id)
    return session.scalars(stmt).one()

def get_user_by_username(username: str):
    stmt = select(User).where(User.username == username).limit(1)
    return session.scalars(stmt).one()

def close_connection():
    session.close()