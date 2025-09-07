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

    def create_default_users(self):
        """Create default users for the application."""
        admin_exists = self.repository.get_by_username('admin') is not None
        website_exists = self.repository.get_by_username('website') is not None

        if not admin_exists:
            admin_user = CreateUserDTO(
                username='admin',
                full_name='Administrator',
                email='admin@example.com',
                password='admin123456',
                role=UserRole.ADMIN,
            )
            self.create_user(admin_user)

        if not website_exists:
            website_user = CreateUserDTO(
                username='website',
                full_name='Website Integration',
                email='website@example.com',
                password='website123456',
                role=UserRole.WEBSITE,
            )
            self.create_user(website_user)

        if admin_exists and website_exists:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Setup has already been completed',
            )
