from typing import Annotated

from fastapi import APIRouter, Depends

from projeto_aplicado.resources.user.service import (
    UserService,
    get_user_service,
)
from projeto_aplicado.settings import get_settings

settings = get_settings()


UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service),
]


router = APIRouter(
    tags=['Setup'],
    prefix='/setup',
    include_in_schema=False,
)


@router.get('/', status_code=200)
async def setup_app(
    user_service: UserServiceDep,
):
    created_users = await user_service.create_default_users()
    return {'created_users': created_users}
