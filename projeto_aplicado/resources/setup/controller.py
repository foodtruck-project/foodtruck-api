from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from projeto_aplicado.resources.user.model import User, UserRole
from projeto_aplicado.resources.user.repository import (
    UserRepository,
    get_user_repository,
)
from projeto_aplicado.resources.user.schemas import (
    CreateUserDTO,
    UserOut,
)
from projeto_aplicado.settings import get_settings

settings = get_settings()
UserRepo = Annotated[UserRepository, Depends(get_user_repository)]
router = APIRouter(tags=['Setup'], prefix=f'{settings.API_PREFIX}/setup')

@router.post(
    '/',
    response_model=UserOut,
    status_code=HTTPStatus.CREATED,
    summary='Cria o primeiro usuário (administrador)',
    description='''
    Cria o primeiro usuário do sistema. Esta rota só pode ser usada uma vez
    e será desativada (retornará 403 Forbidden) se já existir algum usuário no banco de dados.
    Não requer autenticação.
    ''',
    responses={
        201: {
            'description': 'Primeiro usuário administrador criado com sucesso',
            'content': {
                'application/json': {
                    'example': {
                        'id': '1',
                        'username': 'admin',
                        'full_name': 'Admin User',
                        'email': 'admin@example.com',
                        'role': 'admin',
                        'created_at': '2024-03-20T10:00:00',
                        'updated_at': '2024-03-20T10:00:00',
                    }
                }
            },
        },
        403: {
            'description': 'Acesso negado porque o sistema já possui usuários.',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'O sistema já possui usuários. Esta rota foi desativada.',
                    }
                }
            },
        },
        409: {
            'description': 'Conflito de email/usuário',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'Email already registered',
                    }
                }
            },
        },
    },
)
def create_first_user(
    dto: CreateUserDTO,
    repository: UserRepo,
):
    """
    Cria o primeiro usuário do sistema (sem necessidade de autenticação).
    """
    if repository.get_total_count() > 0:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='O sistema já possui usuários. Esta rota foi desativada.',
        )

    user_data = dto.model_dump()
    user_data['role'] = UserRole.ADMIN

    user = User(**user_data)
    repository.create(user)
    return UserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
