import secrets
import string
from http import HTTPStatus
from typing import Sequence

from fastapi import Depends, HTTPException

from projeto_aplicado.ext.cache.redis import get_redis
from projeto_aplicado.resources.base.schemas import Pagination
from projeto_aplicado.resources.user.model import User, UserRole
from projeto_aplicado.resources.user.repository import (
    UserRepository,
    get_user_repository,
)
from projeto_aplicado.resources.user.schemas import (
    CreateUserDTO,
    UpdateUserDTO,
    UserList,
    UserOut,
)
from projeto_aplicado.resources.user.user_cache import (
    UserCache,
    get_user_cache,
)


class UserService:
    def __init__(self, repository: UserRepository, user_cache: UserCache):
        self.repository = repository
        self.user_cache = user_cache

    async def ensure_admin(self, user: User):
        """Ensure the user has admin privileges.

        Args:
            user (User): The user to check.

        Raises:
            HTTPException: (FORBIDDEN) If the user is not an admin.
        """
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='You are not allowed to perform this action',
            )

    async def list_users(self, offset: int, limit: int) -> Sequence[User]:
        cached_users = await self.user_cache.list_users(offset, limit)
        if cached_users:
            return cached_users

        users = self.repository.get_all(offset, limit)
        await self.user_cache.set_user_list(offset, limit, users)
        return users

    async def get_user_by_id(self, user_id: str) -> User:
        cached_user = await self.user_cache.get_user_by_id(user_id)
        if cached_user:
            return cached_user
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='User not found'
            )
        await self.user_cache.set_user(user)
        return user

    async def create_user(self, dto: CreateUserDTO):
        user = User(**dto.model_dump())
        created = self.repository.create(user)
        await self.user_cache.invalidate_list()
        await self.user_cache.invalidate_user(created.id)
        return created

    async def update_user(self, user: User, dto: UpdateUserDTO):
        updated = self.repository.update(
            user, dto.model_dump(exclude_unset=True)
        )
        await self.user_cache.invalidate_user(user.id)
        await self.user_cache.invalidate_list()
        return updated

    async def delete_user(self, user: User) -> None:
        self.repository.delete(user)
        await self.user_cache.invalidate_user(user.id)
        await self.user_cache.invalidate_list()

    async def to_user_out(self, user: User):
        return UserOut(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def to_user_list(
        self, users: Sequence[User], offset: int, limit: int
    ):
        return UserList(
            items=[await self.to_user_out(user) for user in users],
            pagination=await self.get_pagination(offset, limit),
        )

    async def get_pagination(self, offset: int, limit: int):
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

    async def create_default_users(self):
        """Create default users for the application with predictable passwords for Swagger testing."""
        created_users = []

        admin_exists = self.repository.get_by_username('admin') is not None
        website_exists = self.repository.get_by_username('website') is not None

        if not admin_exists:
            admin_password = 'admin123456'
            admin_user = CreateUserDTO(
                username='admin',
                full_name='Administrator',
                email='admin@example.com',
                password=admin_password,
                role=UserRole.ADMIN,
            )
            created = await self.create_user(admin_user)
            created_users.append({
                'username': created.username,
                'email': created.email,
                'role': created.role,
                'password': admin_password,
            })

        if not website_exists:
            website_password = 'website123456'
            website_user = CreateUserDTO(
                username='website',
                full_name='Website Integration',
                email='website@example.com',
                password=website_password,
                role=UserRole.WEBSITE,
            )
            created = await self.create_user(website_user)
            created_users.append({
                'username': created.username,
                'email': created.email,
                'role': created.role,
                'password': website_password,
            })

        if admin_exists and website_exists:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Setup has already been completed',
            )

        return created_users


async def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    redis=Depends(get_redis),
):
    user_cache = get_user_cache(redis)
    return UserService(repo, user_cache)
