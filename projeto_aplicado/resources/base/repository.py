from abc import ABC, abstractmethod
from typing import Generic, Sequence, Type, TypeVar

from sqlmodel import Session, SQLModel, select

T = TypeVar('T', bound=SQLModel)


class AbstractRepository(ABC, Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    @abstractmethod
    def create(self, entity: T) -> T:
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> T | None:
        pass

    @abstractmethod
    def get_all(self, offset: int = 0, limit: int = 100) -> Sequence[T]:
        pass

    @abstractmethod
    def update(self, entity: T, update_data: dict) -> T:
        pass

    @abstractmethod
    def delete(self, entity: T) -> None:
        pass


class BaseRepository(AbstractRepository[T]):
    def __init__(self, session: Session, model: Type[T]):
        super().__init__(session, model)

    def create(self, entity: T) -> T:
        try:
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return entity
        except Exception as e:
            self.session.rollback()
            raise e

    def get_by_id(self, entity_id: str) -> T | None:
        return self.session.get(self.model, entity_id)

    def get_all(self, offset: int = 0, limit: int = 100) -> Sequence[T]:
        stmt = select(self.model).offset(offset).limit(limit)
        return self.session.exec(stmt).all()

    def update(self, entity: T, update_data: dict) -> T:
        try:
            for key, value in update_data.items():
                if value is not None:
                    setattr(entity, key, value)
            self.session.commit()
            self.session.refresh(entity)
            return entity
        except Exception as e:
            self.session.rollback()
            raise e

    def delete(self, entity: T) -> None:
        try:
            self.session.delete(entity)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
