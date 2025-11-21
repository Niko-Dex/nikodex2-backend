import os
import datetime
from dotenv import load_dotenv
from fastapi import UploadFile
from fastapi.responses import FileResponse
from models import Niko, Ability, Blog, Submission, SubmitUser, User, Post
from sqlalchemy.orm import selectinload, sessionmaker, Session
from sqlalchemy import create_engine, desc, select, func, asc
from sqlalchemy.dialects.mysql import insert
from PIL import Image
import io
import dto
from passlib.context import CryptContext
import uuid

load_dotenv()

IMAGE_DIR = os.environ["IMG_DIR"]
MAX_IMG_SIZE = 2 * 1024 * 1024  # 2MB
os.makedirs(IMAGE_DIR, exist_ok=True)

connection_str = "mysql+mysqlconnector://{}:{}@{}:{}/{}".format(
    os.environ["MYSQL_USER"],
    os.environ["MYSQL_PASS"],
    os.environ["MYSQL_URI"],
    os.environ["MYSQL_PORT"],
    "nikodex",
)

engine = create_engine(connection_str, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def run_in_session(func):
    def wrapper(*args, **kwargs):
        session = SessionLocal()
        try:
            result = func(session, *args, **kwargs)
            return result
        except Exception as e:
            print("buh i got an error:")
            print(e)
            session.rollback()
            return None
        finally:
            session.close()

    return wrapper


def get_nikos_wrapper(sort_by: dto.SortType):
    stmt = select(Niko).options(selectinload(Niko.abilities), selectinload(Niko.user))

    if sort_by == dto.SortType.name_ascending:
        stmt = stmt.order_by(asc(Niko.name))
    elif sort_by == dto.SortType.name_descending:
        stmt = stmt.order_by(desc(Niko.name))
    elif sort_by == dto.SortType.recently_added:
        stmt = stmt.order_by(desc(Niko.id))

    return stmt


@run_in_session
def get_all(session: Session, sort_by: dto.SortType):
    stmt = get_nikos_wrapper(sort_by)
    return session.scalars(stmt).fetchall()


@run_in_session
def get_nikos_page(session: Session, page: int, count: int, sort_by: dto.SortType):
    if int(page) < 1:
        return None
    stmt = (
        get_nikos_wrapper(sort_by)
        .offset(int(count) * (int(page) - 1))
        .limit(int(count))
    )
    return session.scalars(stmt).fetchall()


@run_in_session
def get_random_niko(session: Session):
    st_random = select(Niko.id).order_by(func.random()).limit(1).subquery()
    stmt = (
        select(Niko)
        .options(selectinload(Niko.abilities), selectinload(Niko.user))
        .join(st_random, Niko.id == st_random.c.id)
    )
    return session.scalars(stmt).one()


@run_in_session
def get_by_name(session: Session, name: str):
    stmt = (
        select(Niko)
        .options(selectinload(Niko.abilities), selectinload(Niko.user))
        .where(Niko.name.like("%" + name + "%"))
    )
    return session.scalars(stmt).fetchall()


@run_in_session
def get_niko_by_id(session: Session, id: int):
    stmt = select(Niko).options(selectinload(Niko.abilities), selectinload(Niko.user)).where(Niko.id == id)
    res = session.scalars(stmt).one()
    return res


@run_in_session
def get_niko_by_userid(session: Session, user_id: int):
    stmt = (
        select(Niko)
        .options(selectinload(Niko.abilities), selectinload(Niko.user))
        .where(Niko.author_id == user_id)
    )
    res = session.scalars(stmt).fetchall()
    return res


@run_in_session
def get_nikos_count(session: Session):
    return session.query(func.count(Niko.id)).one()[0]

@run_in_session
def get_user_count(session: Session):
    return session.query(func.count(User.id)).one()[0]

@run_in_session
def insert_niko(session: Session, req: dto.NikoRequest):
    stmt = insert(Niko).values(
        name=req.name,
        description=req.description,
        doc="",
        author=req.author,
        full_desc=req.full_desc,
        author_id=req.author_id
    )

    session.execute(stmt)
    session.commit()
    return {"msg": "Inserted Niko."}


@run_in_session
def update_niko(session: Session, id: int, req: dto.NikoRequest, user_id: int):
    entity = session.execute(select(Niko).options(selectinload(Niko.user)).where(Niko.id == id)).scalar_one_or_none()

    allowed = False
    if entity is None:
        return {"msg": "This Niko does not exist.", "err": True}
    if entity.user.id != user_id:
        if entity.user.is_admin:
            allowed = True
    else:
        allowed = True

    if allowed:
        entity.name = req.name
        entity.description = req.description
        entity.full_desc = req.full_desc
        entity.author = req.author
        session.commit()
        return {"msg": "Updated Niko.", "err": False}
    else:
        return {"msg": "Unauthorized", "err": True}


@run_in_session
def delete_niko(session: Session, id: int):
    delete_image(id)
    entity = session.get(Niko, id)
    session.delete(entity)
    session.commit()
    return {"msg": "Deleted Niko."}


@run_in_session
def get_abilities(session: Session):
    stmt = select(Ability)
    return session.scalars(stmt).fetchall()


@run_in_session
def get_ability_by_id(session: Session, id: int):
    stmt = select(Ability).where(Ability.id == id)
    return session.scalars(stmt).one()


@run_in_session
def insert_ability(session: Session, req: dto.AbilityRequest):
    stmt = insert(Ability).values(name=req.name, niko_id=req.niko_id)
    session.execute(stmt)
    session.commit()
    return {"msg": "Inserted Ability."}


@run_in_session
def update_ability(session: Session, id: int, req: dto.AbilityRequest):
    entity = session.execute(
        select(Ability).where(Ability.id == id)
    ).scalar_one_or_none()
    if entity is None:
        return None
    entity.name = req.name
    entity.niko_id = req.niko_id
    session.commit()
    return {"msg": "Updated Ability."}


@run_in_session
def delete_ability(session: Session, id: int):
    entity = session.get(Ability, id)
    session.delete(entity)
    session.commit()
    return {"msg": "Deleted Ability."}


@run_in_session
def get_user_by_username(session: Session, username: str):
    stmt = select(User).where(User.username == username).limit(1)
    return session.scalars(stmt).one()


@run_in_session
def get_blogs(session: Session):
    stmt = select(Blog).order_by(desc(Blog.post_datetime))
    return session.scalars(stmt).fetchall()


@run_in_session
def get_blog_by_id(session: Session, id: int):
    stmt = select(Blog).where(Blog.id == id).limit(1)
    return session.scalars(stmt).one()


@run_in_session
def post_blog(session: Session, req: dto.BlogRequest):
    stmt = insert(Blog).values(
        title=req.title,
        content=req.content,
        author=req.author,
        post_datetime=datetime.datetime.now(),
    )
    session.execute(stmt)
    session.commit()
    return {"msg": "Posted Blog."}


@run_in_session
def update_blog(session: Session, id: int, req: dto.BlogRequest):
    entity = session.execute(select(Blog).where(Blog.id == id)).scalar_one_or_none()
    if entity is None:
        return None
    entity.title = req.title
    entity.content = req.content
    entity.author = req.author
    session.commit()
    return {"msg": "Updated Blog."}


@run_in_session
def delete_blog(session: Session, id: int):
    entity = session.execute(select(Blog).where(Blog.id == id)).scalar_one()
    session.delete(entity)
    session.commit()
    return {"msg": "Deleted Blog."}


@run_in_session
async def upload_image(session: Session, id: int, file: UploadFile):
    entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
    if entity is None:
        return None

    if not file.content_type.startswith("image/"):
        return None
    if file.size > MAX_IMG_SIZE:
        return None
    data = await file.read()
    try:
        image = Image.open(io.BytesIO(data))
    except:
        return None

    image = image.convert("RGBA")
    path = os.path.join(IMAGE_DIR, f"niko-{id}.png")

    image.save(path, format="PNG")

    await file.close()
    entity.image = f"niko-{id}.png"
    session.commit()

    return True


@run_in_session
def delete_image(session: Session, id: int):
    entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
    if entity is None:
        return None

    os.remove(os.path.join(IMAGE_DIR, f"niko-{id}.png"))

    entity.image = ""
    session.commit()
    return True


@run_in_session
def get_image(session: Session, id: int):
    entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
    if entity is None:
        return None

    path = os.path.join(IMAGE_DIR, f"niko-{id}.png")
    if not os.path.exists(path):
        path = os.path.join("images/default.png")
    return FileResponse(path, media_type="image/png")


@run_in_session
def get_submissions(session: Session):
    stmt = select(Submission).order_by(desc(Submission.submit_date))
    return session.scalars(stmt).fetchall()


@run_in_session
def get_submission_by_id(session: Session, id: int):
    stmt = select(Submission).where(Submission.id == id).limit(1)
    return session.scalars(stmt).one()


@run_in_session
def get_submissions_by_userid(session: Session, user_id: int):
    stmt = select(Submission).where(Submission.user_id == user_id)
    return session.scalars(stmt).fetchall()


@run_in_session
def get_submission_image(session: Session, id: int):
    entity = session.execute(select(Submission).where(Submission.id == id)).scalar_one_or_none()
    if entity is None:
        return None
    if len(entity.image) == 0:
        return FileResponse(os.path.join("images/default.png"), media_type="image/png")

    path = os.path.join(IMAGE_DIR, f"{entity.image}")
    if not os.path.exists(path):
        path = os.path.join("images/default.png")
    return FileResponse(path, media_type="image/png")


@run_in_session
async def insert_submission(session: Session, req: dto.SubmitForm, user_id: int, file: UploadFile):
    if not file.content_type.startswith("image/"):
        return False
    if file.size > MAX_IMG_SIZE:
        return False
    data = await file.read()
    try:
        image = Image.open(io.BytesIO(data))
    except:
        return False

    id_str = str(uuid.uuid4())
    image = image.convert("RGBA")
    path = os.path.join(IMAGE_DIR, f"{id_str}.png")

    image.save(path, format="PNG")

    stmt = insert(Submission).values(
        user_id=user_id,
        name=req.name,
        description=req.description,
        full_desc=req.full_desc,
        image=f"{id_str}.png",
        submit_date=datetime.datetime.now(),
    )
    session.execute(stmt)
    session.commit()
    return True


@run_in_session
def delete_submission(session: Session, id: int):
    entity = session.execute(select(Submission).where(Submission.id == id)).scalar_one()

    if (len(entity.image) > 0):
        path = os.path.join(IMAGE_DIR, entity.image)
        if (os.path.exists(path)):
            os.remove(path)

    session.delete(entity)
    session.commit()


@run_in_session
def get_user_by_name(session: Session, username: str):
    stmt = select(User).where(User.username == username)
    return session.scalars(stmt).one()


@run_in_session
def get_user_by_id(session: Session, id: int):
    stmt = select(User).where(User.id == id)
    return session.scalars(stmt).one()


@run_in_session
def get_user_by_usersearch(session: Session, username: str, page: int, count: int):
    stmt = select(User).where(User.username.like(f"%{username}%"))
    stmt = stmt.offset(int(count) * (int(page) - 1)).limit(int(count))
    return session.scalars(stmt).fetchall()


@run_in_session
def insert_user(session: Session, req: dto.UserChangeRequest):
    same_name_entity = session.execute(
        select(User).where(User.username == req.new_username)
    ).scalar_one_or_none()
    if same_name_entity is not None:
        return False

    if len(req.new_username) == 0:
        return False

    if len(req.new_password) == 0:
        return False

    if len(req.new_description) == 0:
        return False

    stmt = insert(User).values(
        username=req.new_username,
        hashed_pass=pwd_context.hash(req.new_password),
        description=req.new_description,
        is_admin=False,
    )

    session.execute(stmt)
    session.commit()
    return True


@run_in_session
def update_user(session: Session, username: str, req: dto.UserChangeRequest):
    same_name_entity = session.execute(
        select(User).where(User.username == req.new_username)
    ).scalar_one_or_none()
    if same_name_entity is not None:
        return False

    entity = session.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()
    if entity is None:
        return False

    if len(req.new_username) > 0:
        entity.username = req.new_username

    if len(req.new_password) > 0:
        entity.hashed_pass = pwd_context.hash(req.new_password)

    if len(req.new_description) > 0:
        entity.description = req.new_description
    session.commit()

    return True


@run_in_session
def get_submit_user(session: Session, user_id: str):
    stmt = select(SubmitUser).where(SubmitUser.user_id == user_id).limit(1)
    return session.scalars(stmt).one_or_none()


@run_in_session
def post_submit_user(session: Session, user_id: str, req: dto.SubmitUserRequest):
    stmt = (
        insert(SubmitUser)
        .values(
            user_id=user_id,
            last_submit_on=req.last_submit_on,
            is_banned=req.is_banned,
            ban_reason=req.ban_reason,
        )
        .on_duplicate_key_update(
            last_submit_on=req.last_submit_on,
            is_banned=req.is_banned,
            ban_reason=req.ban_reason,
        )
    )
    session.execute(stmt)
    session.commit()
    return {"msg": "Updated submit user."}


@run_in_session
def get_posts(session: Session):
    stmt = select(Post).options(selectinload(Post.user))
    return session.scalars(stmt).fetchall()


@run_in_session
def get_post_userid(session: Session, user_id: int):
    stmt = select(Post).where(Post.user_id == user_id).options(selectinload(Post.user))
    return session.scalars(stmt).fetchall()


@run_in_session
def get_post_id(session: Session, id: int):
    stmt = select(Post).where(Post.id == id).options(selectinload(Post.user))
    return session.scalars(stmt).one_or_none()


@run_in_session
def get_post_image(session: Session, id: int):
    entity = session.execute(
        select(Post).where(Post.id == id).options(selectinload(Post.user))
    ).scalar_one_or_none()
    if entity is None:
        return None
    if len(entity.image) == 0:
        return FileResponse(os.path.join("images/default.png"), media_type="image/png")

    path = os.path.join(IMAGE_DIR, f"{entity.image}")
    if not os.path.exists(path):
        path = os.path.join("images/default.png")
    return FileResponse(path, media_type="image/png")


@run_in_session
async def insert_post(session: Session, user_id: int, req: dto.PostRequestForm, file: UploadFile):
    if not file.content_type.startswith("image/"):
        return {"msg": "Not a valid file!", "err": True}
    if file.size > MAX_IMG_SIZE:
        return {"msg": "File too large!", "err": True}
    data = await file.read()
    try:
        image = Image.open(io.BytesIO(data))
    except:
        return {"msg": "Failed to open image!", "err": True}

    id_str = str(uuid.uuid4())
    image = image.convert("RGBA")
    path = os.path.join(IMAGE_DIR, f"{id_str}.png")

    image.save(path, format="PNG")

    stmt = insert(Post).values(
        user_id=user_id,
        title=req.title,
        post_datetime=datetime.datetime.now(),
        content=req.content,
        image=f"{id_str}.png"
    );

    session.execute(stmt)
    session.commit()
    return {"msg": "Inserted Post.", "err": False}


def close_connection():
    SessionLocal.close_all()
