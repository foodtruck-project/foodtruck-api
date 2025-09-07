from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends

from projeto_aplicado.auth.security import get_current_user
from projeto_aplicado.resources.user.model import User
from projeto_aplicado.resources.user.schemas import (
    CreateUserDTO,
    UpdateUserDTO,
    UserList,
    UserOut,
)
from projeto_aplicado.resources.user.service import (
    UserService,
    get_user_service,
)
from projeto_aplicado.settings import get_settings

settings = get_settings()

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(tags=['Usuários'], prefix=f'{settings.API_PREFIX}/users')


@router.get('/', response_model=UserList, status_code=HTTPStatus.OK)
async def fetch_users(
    service: UserServiceDep,
    current_user: CurrentUser,
    offset: int = 0,
    limit: int = 100,
):
    """Lista usuários do sistema com paginação."""
    await service.ensure_admin(current_user)
    users = await service.list_users(offset=offset, limit=limit)
    user_list = await service.to_user_list(users, offset, limit)
    return user_list


@router.get('/{user_id}', response_model=UserOut)
async def fetch_user_by_id(
    user_id: str, service: UserServiceDep, current_user: CurrentUser
):
    """Busca usuário pelo ID."""
    await service.ensure_admin(current_user)
    user = await service.get_user_by_id(user_id)
    user_out = await service.to_user_out(user)
    return user_out


@router.post('/', response_model=UserOut, status_code=HTTPStatus.CREATED)
async def create_user(
    dto: CreateUserDTO,
    service: UserServiceDep,
    current_user: CurrentUser,
):
    """Cria um novo usuário"""
    await service.ensure_admin(current_user)
    user = await service.create_user(dto)
    user_out = await service.to_user_out(user)
    return user_out


@router.patch('/{user_id}', response_model=UserOut)
async def update_user(
    user_id: str,
    dto: UpdateUserDTO,
    service: UserServiceDep,
    current_user: CurrentUser,
):
    """Atualiza um usuário pelo ID"""
    await service.ensure_admin(current_user)
    existing_user = await service.get_user_by_id(user_id)
    updated_user = await service.update_user(existing_user, dto)
    user_out = await service.to_user_out(updated_user)
    return user_out


@router.delete('/{user_id}', status_code=HTTPStatus.OK)
async def delete_user(
    user_id: str,
    service: UserServiceDep,
    current_user: CurrentUser,
):
    """Remove um usuário pelo ID"""
    await service.ensure_admin(current_user)
    user = await service.get_user_by_id(user_id)
    await service.delete_user(user)
    return {'action': 'deleted', 'id': user_id}
