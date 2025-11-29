from datetime import datetime, timedelta

from sqlalchemy import (
    asc,
    delete,
    desc,
    exists,
    func,
    select,
)
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import selectinload

from common.dto import (
    NikoRequest,
    SortType,
)
from common.models import Niko, Notd, User
from services._shared import SessionManager
from services.images import delete_image


def get_nikos_wrapper(sort_by: SortType):
    stmt = select(Niko).options(selectinload(Niko.abilities), selectinload(Niko.user))

    if sort_by == SortType.name_ascending:
        stmt = stmt.order_by(asc(Niko.name))
    elif sort_by == SortType.name_descending:
        stmt = stmt.order_by(desc(Niko.name))
    elif sort_by == SortType.recently_added:
        stmt = stmt.order_by(desc(Niko.id))

    return stmt


def get_all(sort_by: SortType):
    with SessionManager() as session:
        stmt = get_nikos_wrapper(sort_by)
        return session.scalars(stmt).fetchall()


def get_nikos_page(page: int, count: int, sort_by: SortType):
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


def insert_niko(req: NikoRequest):
    with SessionManager() as session:
        stmt = insert(Niko).values(
            name=req.name,
            description=req.description,
            doc="",
            author="",
            full_desc=req.full_desc,
            author_id=req.author_id,
            is_blacklisted=req.is_blacklisted,
        )

        session.execute(stmt)
        session.commit()
        return {"msg": "Inserted Niko."}


def update_niko(id: int, req: NikoRequest, user_id: int):
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
            entity.is_blacklisted = req.is_blacklisted
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
