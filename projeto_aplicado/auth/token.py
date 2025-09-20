from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing_extensions import Annotated

from projeto_aplicado.auth.password import verify_password
from projeto_aplicado.auth.security import create_access_token
from projeto_aplicado.resources.user.repository import (
    UserRepository,
    get_user_repository,
)
from projeto_aplicado.settings import get_settings

settings = get_settings()
router = APIRouter(tags=['Token'])

user_repository_dep = Annotated[UserRepository, Depends(get_user_repository)]


def validate_user_credentials(
    user_repository: UserRepository, username: str, password: str
):
    user = user_repository.get_by_username(username)

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect username or password',
        )

    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect username or password',
        )

    return user


@router.post(
    f'{settings.API_PREFIX}/token',
    response_model=dict,
    status_code=HTTPStatus.OK,
)
async def create_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repository: user_repository_dep,
):
    if not form_data.username or not form_data.username.strip():
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='Username cannot be empty',
        )

    if not form_data.password or not form_data.password.strip():
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='Password cannot be empty',
        )

    try:
        user = validate_user_credentials(
            user_repository, form_data.username, form_data.password
        )
        access_token = create_access_token(data={'sub': user.username})

        return {
            'access_token': access_token,
            'token_type': 'bearer',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
            },
        }
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect username or password',
        )
