from http import HTTPStatus
from typing import Sequence

from fastapi import HTTPException

from projeto_aplicado.resources.base.schemas import Pagination
from projeto_aplicado.resources.user.model import User, UserRole
from projeto_aplicado.resources.user.repository import UserRepository
from projeto_aplicado.resources.user.schemas import (
    CreateUserDTO,
    UpdateUserDTO,
    UserList,
    UserOut,
)


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def ensure_admin(self, user: User):
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='You are not allowed to perform this action',
            )

    def list_users(self, offset: int, limit: int) -> Sequence[User]:
        return self.repository.get_all(offset=offset, limit=limit)

    def get_user_by_id(self, user_id: str) -> User:
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='User not found'
            )
        return user

    def create_user(self, dto: CreateUserDTO) -> User:
        user = User(**dto.model_dump())
        return self.repository.create(user)

    def update_user(self, user: User, dto: UpdateUserDTO) -> User:
        return self.repository.update(user, dto.model_dump(exclude_unset=True))

    def delete_user(self, user: User) -> None:
        self.repository.delete(user)

    def to_user_out(self, user: User) -> UserOut:
        return UserOut(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def to_user_list(
        self, users: Sequence[User], offset: int, limit: int
    ) -> UserList:
        return UserList(
            items=[self.to_user_out(user) for user in users],
            pagination=self.get_pagination(offset, limit),
        )

    def get_pagination(self, offset: int, limit: int):
        total = self.repository.get_total_count()
        page = (offset // limit) + 1 if limit else 1
        total_pages = (
            (total // limit) + (1 if total % limit else 0) if limit else 1
        )
        return Pagination(
            offset=offset,
            limit=limit,
            total_count=total,
            total_pages=total_pages,
            page=page,
        )
