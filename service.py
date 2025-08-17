import os
import datetime
from dotenv import load_dotenv
from models import Niko, Ability, Blog, User
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
    try:
        stmt = select(Niko).options(selectinload(Niko.abilities)).where(Niko.id == id)
        res = session.scalars(stmt).one()
        return res
    except:
        return None

def get_nikos_count():
    return session.query(func.count(Niko.id)).one()[0]

def insert_niko(req: dto.NikoRequest):
    stmt = insert(Niko).values(name=req.name, description=req.description,
        image=req.image, doc="", author=req.author, full_desc=req.full_desc)
    
    result = session.execute(stmt)
    session.commit()
    
def update_niko(id: int, req: dto.NikoRequest):
    entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one()
    entity.name = req.name
    entity.description = req.description
    entity.image = req.image
    entity.full_desc = req.full_desc
    entity.author = req.author
    session.commit()
    
def delete_niko(id: int):
    entity = session.get(Niko, id)
    session.delete(entity)
    session.commit()

def get_abilities():
    stmt = select(Ability)
    return session.scalars(stmt).fetchall()

def get_ability_by_id(id: int):
    stmt = select(Ability).where(Ability.id == id)
    return session.scalars(stmt).one()

def insert_ability(req: dto.AbilityRequest):
    stmt = insert(Ability).values(name=req.name, niko_id=req.niko_id)
    result = session.execute(stmt)
    session.commit()
    
def update_ability(id: int, req: dto.AbilityRequest):
    entity = session.execute(select(Ability).where(Ability.id == id)).scalar_one()
    entity.name = req.name
    entity.niko_id = req.niko_id
    session.commit()
    
def delete_ability(id: int):
    entity = session.get(Ability, id)
    session.delete(entity)
    session.commit()

def get_user_by_username(username: str):
    stmt = select(User).where(User.username == username).limit(1)
    return session.scalars(stmt).one()

def get_blogs():
    stmt = select(Blog)
    return session.scalars(stmt).fetchall()

def get_blog_by_id(id: int):
    stmt = select(Blog).where(Blog.id == id).limit(1)
    return session.scalars(stmt).one()

def post_blog(req: dto.BlogRequest):
    stmt = insert(Blog).values(title=req.title, content=req.content,
        author=req.author, post_datetime=datetime.datetime.now())
    result = session.execute(stmt)
    session.commit()
    
def update_blog(id: int, req: dto.BlogRequest):
    entity = session.execute(select(Blog).where(Blog.id == id)).scalar_one()
    entity.title = req.title
    entity.content = req.content
    entity.author = req.author
    session.commit()
    
def delete_blog(id: int):
    entity = session.execute(select(Blog).where(Blog.id == id)).scalar_one()
    session.delete(entity)
    session.commit()

def close_connection():
    session.close()