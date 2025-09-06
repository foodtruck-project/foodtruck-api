from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, func, select

from projeto_aplicado.ext.database.db import get_session
from projeto_aplicado.resources.base.repository import (
    BaseRepository,
)
from projeto_aplicado.resources.user.model import User


def get_user_repository(session: Annotated[Session, Depends(get_session)]):
    return UserRepository(session)


class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session):
        super().__init__(model=User, session=session)

    def get_total_count(self) -> int:
        stmt = select(func.count()).select_from(User)
        return self.session.exec(stmt).one()

    def create(self, entity):
        return super().create(entity)

    def get_by_id(self, entity_id):
        return super().get_by_id(entity_id)

    def get_all(self, offset: int = 0, limit: int = 100):
        return super().get_all(offset, limit)

    def get_by_email(self, email: str):
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def get_by_username(self, username: str):
        statement = select(User).where(User.username == username)
        return self.session.exec(statement).first()

    def update(self, entity, update_data):
        return super().update(entity, update_data)

    def delete(self, entity):
        return super().delete(entity)
