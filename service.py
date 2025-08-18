import os
import datetime
from dotenv import load_dotenv
from models import Niko, Ability, Blog, User
from sqlalchemy.orm import Session, selectinload, sessionmaker
from sqlalchemy import and_, create_engine, text, select, insert, func
import dto

load_dotenv()

connection_str = "mysql+mysqlconnector://{}:{}@{}:{}/{}" \
    .format(os.environ['MYSQL_USER'], os.environ['MYSQL_PASS'], os.environ['MYSQL_URI'], os.environ['MYSQL_PORT'], "nikodex")

engine = create_engine(connection_str, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

def run_in_session(func):
    def wrapper(*args, **kwargs):
        session = SessionLocal()
        try:
            result = func(session, *args, **kwargs)
            return result
        except:
            print("buh")
            session.rollback()
            return None
        finally:
            session.close()
    return wrapper

@run_in_session
def get_all(session):
    stmt = select(Niko).options(selectinload(Niko.abilities))
    return session.scalars(stmt).fetchall()

@run_in_session
def get_by_name(session, name: str):
    stmt = select(Niko).options(selectinload(Niko.abilities)).where(Niko.name.like(name))
    return session.scalars(stmt).fetchall()

@run_in_session
def get_niko_by_id(session, id: int):
    stmt = select(Niko).options(selectinload(Niko.abilities)).where(Niko.id == id)
    res = session.scalars(stmt).one()
    return res

@run_in_session
def get_nikos_count(session):
    return session.query(func.count(Niko.id)).one()[0]

@run_in_session
def insert_niko(session, req: dto.NikoRequest):
    stmt = insert(Niko).values(name=req.name, description=req.description,
    image=req.image, doc="", author=req.author, full_desc=req.full_desc)

    session.execute(stmt)
    session.commit()
    return {"msg":"Inserted Niko."}

@run_in_session
def update_niko(session, id: int, req: dto.NikoRequest):
    entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
    if entity is None:
        return None
    entity.name = req.name
    entity.description = req.description
    entity.image = req.image
    entity.full_desc = req.full_desc
    entity.author = req.author
    session.commit()
    return {"msg":"Updated Niko."}

@run_in_session
def delete_niko(session, id: int):
    entity = session.get(Niko, id)
    session.delete(entity)
    session.commit()
    return {"msg":"Deleted Niko."}

@run_in_session
def get_abilities(session):
    stmt = select(Ability)
    return session.scalars(stmt).fetchall()

@run_in_session
def get_ability_by_id(session, id: int):
    stmt = select(Ability).where(Ability.id == id)
    return session.scalars(stmt).one()

@run_in_session
def insert_ability(session, req: dto.AbilityRequest):
    stmt = insert(Ability).values(name=req.name, niko_id=req.niko_id)
    session.execute(stmt)
    session.commit()
    return {"msg":"Inserted Ability."}

@run_in_session
def update_ability(session, id: int, req: dto.AbilityRequest):
    entity = session.execute(select(Ability).where(Ability.id == id)).scalar_one_or_none()
    if entity is None:
        return None
    entity.name = req.name
    entity.niko_id = req.niko_id
    session.commit()
    return {"msg":"Updated Ability."}

@run_in_session
def delete_ability(session, id: int):
    entity = session.get(Ability, id)
    session.delete(entity)
    session.commit()
    return {"msg":"Deleted Ability."}

@run_in_session
def get_user_by_username(session, username: str):
    stmt = select(User).where(User.username == username).limit(1)
    return session.scalars(stmt).one()

@run_in_session
def get_blogs(session, ):
    stmt = select(Blog)
    return session.scalars(stmt).fetchall()

@run_in_session
def get_blog_by_id(session, id: int):
    stmt = select(Blog).where(Blog.id == id).limit(1)
    return session.scalars(stmt).one()

@run_in_session
def post_blog(session, req: dto.BlogRequest):
    stmt = insert(Blog).values(title=req.title, content=req.content,
        author=req.author, post_datetime=datetime.datetime.now())
    session.execute(stmt)
    session.commit()
    return {"msg":"Posted Blog."}

@run_in_session
def update_blog(session, id: int, req: dto.BlogRequest):
    entity = session.execute(select(Blog).where(Blog.id == id)).scalar_one_or_none()
    if entity is None:
        return None
    entity.title = req.title
    entity.content = req.content
    entity.author = req.author
    session.commit()
    return {"msg":"Updated Blog."}

@run_in_session
def delete_blog(session, id: int):
    entity = session.execute(select(Blog).where(Blog.id == id)).scalar_one()
    session.delete(entity)
    session.commit()
    return {"msg":"Deleted Blog."}

def close_connection():
    SessionLocal.close_all()