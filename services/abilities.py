from sqlalchemy import (
    select,
)
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import selectinload

from common.dto import (
    AbilityRequest,
)
from common.models import Ability, Niko, User
from services._shared import SessionManager


def get_abilities():
    with SessionManager() as session:
        stmt = select(Ability)
        return session.scalars(stmt).fetchall()


def get_ability_by_id(id: int):
    with SessionManager() as session:
        stmt = select(Ability).where(Ability.id == id)
        return session.scalars(stmt).one()


def insert_ability(req: AbilityRequest, user_id: int):
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


def update_ability(id: int, req: AbilityRequest, user_id: int):
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
