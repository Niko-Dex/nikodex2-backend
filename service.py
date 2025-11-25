import io
import os
import uuid
from datetime import datetime, timedelta
from types import TracebackType
from typing import Optional, Type

from dotenv import load_dotenv
from fastapi import UploadFile
from fastapi.responses import FileResponse
from passlib.context import CryptContext
from PIL import Image
from sqlalchemy import (
    asc,
    create_engine,
    delete,
    desc,
    exists,
    func,
    select,
)
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import selectinload, sessionmaker

import dto
from models import Ability, Blog, Niko, Notd, Post, Submission, SubmitUser, User

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


class SessionManager:
    def __enter__(self):
        self.session = SessionLocal()
        return self.session

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ):
        if exc_type:
            print("ERR in DB!")
            print(exc_value)
            self.session.rollback()
            return False

        self.session.close()


def get_nikos_wrapper(sort_by: dto.SortType):
    stmt = select(Niko).options(selectinload(Niko.abilities), selectinload(Niko.user))

    if sort_by == dto.SortType.name_ascending:
        stmt = stmt.order_by(asc(Niko.name))
    elif sort_by == dto.SortType.name_descending:
        stmt = stmt.order_by(desc(Niko.name))
    elif sort_by == dto.SortType.recently_added:
        stmt = stmt.order_by(desc(Niko.id))

    return stmt


def get_all(sort_by: dto.SortType):
    with SessionManager() as session:
        stmt = get_nikos_wrapper(sort_by)
        return session.scalars(stmt).fetchall()


def get_nikos_page(page: int, count: int, sort_by: dto.SortType):
    with SessionManager() as session:
        if int(page) < 1:
            return None
        stmt = (
            get_nikos_wrapper(sort_by)
            .offset(int(count) * (int(page) - 1))
            .limit(int(count))
        )
        return session.scalars(stmt).fetchall()


def get_random_niko():
    with SessionManager() as session:
        st_random = select(Niko.id).order_by(func.random()).limit(1).subquery()
        stmt = (
            select(Niko)
            .options(selectinload(Niko.abilities), selectinload(Niko.user))
            .join(st_random, Niko.id == st_random.c.id)
        )
        return session.scalars(stmt).one()


def get_notd():
    with SessionManager() as session:
        cnt_stmt = select(func.count()).select_from(Niko)
        cnt = session.scalar(cnt_stmt)
        if cnt is None or cnt <= 0:
            return None

        latest_chosen_notd_stmt = select(Notd).order_by(desc(Notd.chosen_at)).limit(1)
        latest_chosen_notd = session.scalars(latest_chosen_notd_stmt).all()
        latest_chosen_ts = latest_chosen_notd[0].chosen_at
        refresh_ts = datetime(
            latest_chosen_ts.year, latest_chosen_ts.month, latest_chosen_ts.day
        ) + timedelta(days=1)

        if len(latest_chosen_notd) > 0:
            now_ts = datetime.now()
            # not time to refresh yet
            if now_ts < refresh_ts:
                return (get_niko_by_id(id=latest_chosen_notd[0].niko_id), refresh_ts)

        # either db is empty, or it's time to refresh
        new_notd: Niko | None = None
        while True:  #! quite dangerous...
            new_notd_stmt = (
                select(Niko)
                .where(~exists().where(Notd.niko_id == Niko.id))
                .order_by(func.random())
                .limit(1)
            )
            new_notd_list = session.scalars(new_notd_stmt).all()
            if len(new_notd_list) <= 0:
                wipe_notd_stmt = delete(Notd).where(Notd.niko_id > -1)
                session.execute(wipe_notd_stmt)
                session.commit()
            else:
                new_notd = new_notd_list[0]
                break

        new_notd_insert_stmt = insert(Notd).values(niko_id=new_notd.id)
        session.execute(new_notd_insert_stmt)
        session.commit()
        return (get_niko_by_id(id=new_notd.id), refresh_ts)


def get_by_name(name: str):
    with SessionManager() as session:
        stmt = (
            select(Niko)
            .options(selectinload(Niko.abilities), selectinload(Niko.user))
            .where(Niko.name.like("%" + name + "%"))
        )
        return session.scalars(stmt).fetchall()


def get_niko_by_id(id: int):
    with SessionManager() as session:
        stmt = (
            select(Niko)
            .options(selectinload(Niko.abilities), selectinload(Niko.user))
            .where(Niko.id == id)
        )
        res = session.scalars(stmt).one()
        return res


def get_niko_by_userid(user_id: int):
    with SessionManager() as session:
        stmt = (
            select(Niko)
            .options(selectinload(Niko.abilities), selectinload(Niko.user))
            .where(Niko.author_id == user_id)
        )
        res = session.scalars(stmt).fetchall()
        return res


def get_nikos_count():
    with SessionManager() as session:
        return session.query(func.count(Niko.id)).one()[0]


def get_user_count():
    with SessionManager() as session:
        return session.query(func.count(User.id)).one()[0]


def insert_niko(req: dto.NikoRequest):
    with SessionManager() as session:
        stmt = insert(Niko).values(
            name=req.name,
            description=req.description,
            doc="",
            author="",
            full_desc=req.full_desc,
            author_id=req.author_id,
        )

        session.execute(stmt)
        session.commit()
        return {"msg": "Inserted Niko."}


def update_niko(id: int, req: dto.NikoRequest, user_id: int):
    with SessionManager() as session:
        user_entity = session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()
        entity = session.execute(
            select(Niko).options(selectinload(Niko.user)).where(Niko.id == id)
        ).scalar_one_or_none()

        allowed = False
        if entity is None:
            return {"msg": "This Niko does not exist.", "err": True}
        if user_entity is None:
            return {"msg": "Who are you?", "err": True}

        if entity.user is None:
            if user_entity.is_admin:
                allowed = True
        else:
            if entity.user.id != user_id:
                if user_entity.is_admin:
                    allowed = True
            else:
                allowed = True

        if allowed:
            entity.name = req.name
            entity.description = req.description
            entity.full_desc = req.full_desc
            if req.author_id is not None and req.author_id >= 0:
                specified_author = session.execute(
                    select(User).where(User.id == req.author_id)
                ).scalar_one_or_none()
                if specified_author is None:
                    return {"msg": "Specified author ID does not exist.", "err": True}
                entity.author_id = req.author_id
            else:
                entity.author_id = None
            session.commit()
            return {"msg": "Updated Niko.", "err": False}
        else:
            return {"msg": "Unauthorized", "err": True}


def delete_niko(id: int):
    with SessionManager() as session:
        delete_image(id)
        entity = session.get(Niko, id)
        if entity is None:
            return None
        else:
            session.delete(entity)
            session.commit()
            return entity


def get_abilities():
    with SessionManager() as session:
        stmt = select(Ability)
        return session.scalars(stmt).fetchall()


def get_ability_by_id(id: int):
    with SessionManager() as session:
        stmt = select(Ability).where(Ability.id == id)
        return session.scalars(stmt).one()


def insert_ability(req: dto.AbilityRequest, user_id: int):
    with SessionManager() as session:
        niko_entity = session.execute(
            select(Niko).where(Niko.id == req.niko_id).options(selectinload(Niko.user))
        ).scalar_one_or_none()
        user_entity = session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()
        if niko_entity is None:
            return {"msg": "This Niko is not found.", "err": True}

        allowed = False
        if user_entity and user_entity.is_admin:
            allowed = True
        else:
            if niko_entity.user is None:
                return {"msg": "This Niko does not belong to a user.", "err": True}
            else:
                if niko_entity.user.id == user_id:
                    allowed = True

        if allowed:
            stmt = insert(Ability).values(name=req.name, niko_id=req.niko_id)
            session.execute(stmt)
            session.commit()
            return {"msg": "Inserted Ability.", "err": False}
        else:
            return {"msg": "Unauthorized.", "err": False}


def update_ability(id: int, req: dto.AbilityRequest, user_id: int):
    with SessionManager() as session:
        user_entity = session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()
        entity = session.execute(
            select(Ability).where(Ability.id == id).options(selectinload(Ability.niko))
        ).scalar_one_or_none()
        if entity is None:
            return None

        allowed = False
        if user_entity is None:
            return {"msg": "Who are you?", "err": True}
        else:
            if entity.niko is None:
                return {"msg": "This Ability does not belong to a Niko :/", "err": True}

            if user_entity.is_admin:
                allowed = True
            else:
                if entity.niko.author_id == user_id:
                    allowed = True

        if allowed:
            entity.name = req.name
            entity.niko_id = req.niko_id
            session.commit()
            return {"msg": "Updated Ability.", "err": False}
        else:
            return {"msg": "Unauthorized", "err": True}


def delete_ability(id: int, user_id: int):
    with SessionManager() as session:
        entity = session.get(Ability, id)
        if entity is None:
            return None

        allowed = False
        niko_entity = session.execute(
            select(Niko)
            .where(Niko.id == entity.niko_id)
            .options(selectinload(Niko.user))
        ).scalar_one_or_none()
        user_entity = session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

        if niko_entity is None:
            return {"msg": "This Niko does not exist.", "err": True}

        if user_entity is None:
            return {"msg": "This user does not exist.", "err": True}

        if niko_entity.user is None:
            if user_entity.is_admin:
                allowed = True
        else:
            if user_entity.is_admin or niko_entity.user.id == user_id:
                allowed = True

        if allowed:
            session.delete(entity)
            session.commit()
            return entity
        else:
            return {"msg": "Unauthorized.", "err": True}


def get_user_by_username(username: str):
    with SessionManager() as session:
        stmt = select(User).where(User.username == username).limit(1)
        return session.scalars(stmt).one()


def get_blogs():
    with SessionManager() as session:
        stmt = select(Blog).order_by(desc(Blog.post_datetime))
        return session.scalars(stmt).fetchall()


def get_blog_by_id(id: int):
    with SessionManager() as session:
        stmt = select(Blog).where(Blog.id == id).limit(1)
        return session.scalars(stmt).one()


def post_blog(req: dto.BlogRequest):
    with SessionManager() as session:
        stmt = insert(Blog).values(
            title=req.title,
            content=req.content,
            author=req.author,
            post_datetime=datetime.now(),
        )
        session.execute(stmt)
        session.commit()
        return {"msg": "Posted Blog."}


def update_blog(id: int, req: dto.BlogRequest):
    with SessionManager() as session:
        entity = session.execute(select(Blog).where(Blog.id == id)).scalar_one_or_none()
        if entity is None:
            return None
        entity.title = req.title
        entity.content = req.content
        entity.author = req.author
        session.commit()
        return {"msg": "Updated Blog."}


def delete_blog(id: int):
    with SessionManager() as session:
        entity = session.execute(select(Blog).where(Blog.id == id)).scalar_one()
        if entity is None:
            return None
        else:
            session.delete(entity)
            session.commit()
            return entity


async def upload_image(id: int, file: UploadFile):
    with SessionManager() as session:
        entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
        if entity is None:
            return None

        if not file.content_type or not file.content_type.startswith("image/"):
            return None
        if not file.size or file.size > MAX_IMG_SIZE:
            return None
        data = await file.read()
        try:
            image = Image.open(io.BytesIO(data))
        except Exception:
            return None

        image = image.convert("RGBA")
        path = os.path.join(IMAGE_DIR, f"niko-{id}.png")

        image.save(path, format="PNG")

        await file.close()
        session.commit()

        return True


def delete_image(id: int):
    with SessionManager() as session:
        entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
        if entity is None:
            return None

        try:
            os.remove(os.path.join(IMAGE_DIR, f"niko-{id}.png"))
        except Exception:
            return None

        session.commit()
        return True


def get_image(id: int):
    with SessionManager() as session:
        entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
        if entity is None:
            return None

        path = os.path.join(IMAGE_DIR, f"niko-{id}.png")
        if not os.path.exists(path):
            path = os.path.join("images/default.png")
        return FileResponse(path, media_type="image/png")


def get_submissions():
    with SessionManager() as session:
        stmt = select(Submission).order_by(desc(Submission.submit_date))
        return session.scalars(stmt).fetchall()


def get_submission_by_id(id: int):
    with SessionManager() as session:
        stmt = select(Submission).where(Submission.id == id).limit(1)
        return session.scalars(stmt).one()


def get_submissions_by_userid(user_id: int):
    with SessionManager() as session:
        stmt = select(Submission).where(Submission.user_id == user_id)
        return session.scalars(stmt).fetchall()


def get_submission_image(id: int):
    with SessionManager() as session:
        entity = session.execute(
            select(Submission).where(Submission.id == id)
        ).scalar_one_or_none()
        if entity is None:
            return None
        if len(entity.image) == 0:
            return FileResponse(
                os.path.join("images/default.png"), media_type="image/png"
            )

        path = os.path.join(IMAGE_DIR, f"{entity.image}")
        if not os.path.exists(path):
            path = os.path.join("images/default.png")
        return FileResponse(path, media_type="image/png")


async def insert_submission(req: dto.SubmitForm, user_id: int, file: UploadFile):
    with SessionManager() as session:
        if not file.content_type or not file.content_type.startswith("image/"):
            return False
        if not file.size or file.size > MAX_IMG_SIZE:
            return False
        data = await file.read()
        try:
            image = Image.open(io.BytesIO(data))
        except Exception:
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
            submit_date=datetime.now(),
        )
        session.execute(stmt)
        session.commit()
        return True


def delete_submission(id: int):
    with SessionManager() as session:
        entity = session.execute(
            select(Submission).where(Submission.id == id)
        ).scalar_one()

        if len(entity.image) > 0:
            path = os.path.join(IMAGE_DIR, entity.image)
            if os.path.exists(path):
                os.remove(path)

        session.delete(entity)
        session.commit()


def get_user_by_name(username: str):
    with SessionManager() as session:
        stmt = select(User).where(User.username == username)
        return session.scalars(stmt).one()


def get_user_by_id(id: int):
    with SessionManager() as session:
        stmt = select(User).where(User.id == id)
        return session.scalars(stmt).one()


def get_user_by_usersearch(username: str, page: int, count: int):
    with SessionManager() as session:
        stmt = select(User).where(User.username.like(f"%{username}%"))
        stmt = stmt.offset(int(count) * (int(page) - 1)).limit(int(count))
        return session.scalars(stmt).fetchall()


def insert_user(req: dto.UserChangeRequest):
    with SessionManager() as session:
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


def update_user(username: str, req: dto.UserChangeRequest):
    with SessionManager() as session:
        same_name_entity = session.execute(
            select(User).where(User.username == req.new_username)
        ).scalar_one_or_none()
        same_description_entity = session.execute(
            select(User).where(User.description.like(f"%{req.new_description}%"))
        ).scalar_one_or_none()
        if same_name_entity is not None and same_description_entity is not None:
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


def get_submit_user(user_id: str):
    with SessionManager() as session:
        stmt = select(SubmitUser).where(SubmitUser.user_id == user_id).limit(1)
        return session.scalars(stmt).one_or_none()


def post_submit_user(user_id: str, req: dto.SubmitUserRequest):
    with SessionManager() as session:
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


def get_posts():
    with SessionManager() as session:
        stmt = select(Post).options(selectinload(Post.user))
        return session.scalars(stmt).fetchall()


def get_post_userid(user_id: int):
    with SessionManager() as session:
        stmt = (
            select(Post).where(Post.user_id == user_id).options(selectinload(Post.user))
        )
        return session.scalars(stmt).fetchall()


def get_post_id(id: int):
    with SessionManager() as session:
        stmt = select(Post).where(Post.id == id).options(selectinload(Post.user))
        return session.scalars(stmt).one_or_none()


def get_post_image(id: int):
    with SessionManager() as session:
        entity = session.execute(
            select(Post).where(Post.id == id).options(selectinload(Post.user))
        ).scalar_one_or_none()
        if entity is None:
            return None
        if len(entity.image) == 0:
            return FileResponse(
                os.path.join("images/default.png"), media_type="image/png"
            )

        path = os.path.join(IMAGE_DIR, f"{entity.image}")
        if not os.path.exists(path):
            path = os.path.join("images/default.png")
        return FileResponse(path, media_type="image/png")


async def insert_post(user_id: int, req: dto.PostRequestForm, file: UploadFile):
    with SessionManager() as session:
        if not file.content_type or not file.content_type.startswith("image/"):
            return {"msg": "Not a valid file!", "err": True}
        if not file.size or file.size > MAX_IMG_SIZE:
            return {"msg": "File too large!", "err": True}
        data = await file.read()
        try:
            image = Image.open(io.BytesIO(data))
        except Exception:
            return {"msg": "Failed to open image!", "err": True}

        id_str = str(uuid.uuid4())
        image = image.convert("RGBA")
        path = os.path.join(IMAGE_DIR, f"{id_str}.png")

        image.save(path, format="PNG")

        stmt = insert(Post).values(
            user_id=user_id,
            title=req.title,
            post_datetime=datetime.now(),
            content=req.content,
            image=f"{id_str}.png",
        )

        session.execute(stmt)
        session.commit()
        return {"msg": "Inserted Post.", "err": False}


def close_connection():
    SessionLocal.close_all()
