from typing import Annotated

from fastapi import APIRouter, Depends

from projeto_aplicado.resources.user.repository import (
    UserRepository,
    get_user_repository,
)
from projeto_aplicado.resources.user.service import UserService
from projeto_aplicado.settings import get_settings

settings = get_settings()

UserRepo = Annotated[UserRepository, Depends(get_user_repository)]


def get_user_service(user_repo: UserRepo) -> UserService:
    return UserService(repository=user_repo)


UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service),
]
router = APIRouter(tags=['Setup'], prefix=f'{settings.API_PREFIX}/setup')


@router.get('/setup', status_code=200)
def setup_app(user_service: UserServiceDep):
    user_service.create_default_users()
