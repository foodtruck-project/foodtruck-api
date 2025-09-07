from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends

from projeto_aplicado.auth.security import get_current_user
from projeto_aplicado.ext.cache.redis import get_redis
from projeto_aplicado.resources.user.model import User
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
from projeto_aplicado.resources.user.service import UserService
from projeto_aplicado.settings import get_settings

settings = get_settings()


async def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    redis=Depends(get_redis),
) -> UserService:
    return UserService(repo, redis)


UserSvc = Annotated[UserService, Depends(get_user_service)]
router = APIRouter(tags=['Usuários'], prefix=f'{settings.API_PREFIX}/users')
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get(
    '/',
    response_model=UserList,
    status_code=HTTPStatus.OK,
    summary='Listar usuários',
    description="""
    Retorna uma lista paginada de usuários do sistema. Apenas administradores podem acessar este endpoint.

    **Parâmetros:**
    - **offset**: Número de registros para pular (padrão: 0)
    - **limit**: Limite de registros por página (padrão: 100)

    **Exemplo de requisição:**
    ```bash
    curl -X GET \
      -H "Authorization: Bearer <token>" \
      "http://localhost:8000/api/v1/users?offset=0&limit=10"
    ```
    """,  # noqa: E501
    responses={
        200: {
            'description': 'Lista de usuários retornada com sucesso',
            'content': {
                'application/json': {
                    'examples': {
                        'async default': {
                            'summary': 'Exemplo de resposta',
                            'value': {
                                'items': [
                                    {
                                        'id': '1',
                                        'username': 'admin',
                                        'full_name': 'Admin User',
                                        'email': 'admin@example.com',
                                        'role': 'admin',
                                        'created_at': '2024-03-20T10:00:00',
                                        'updated_at': '2024-03-20T10:00:00',
                                    },
                                    {
                                        'id': '2',
                                        'username': 'attendant',
                                        'full_name': 'Attendant User',
                                        'email': 'attendant@example.com',
                                        'role': 'attendant',
                                        'created_at': '2024-03-20T10:00:00',
                                        'updated_at': '2024-03-20T10:00:00',
                                    },
                                ],
                                'pagination': {
                                    'offset': 0,
                                    'limit': 100,
                                    'total_count': 2,
                                    'total_pages': 1,
                                    'page': 1,
                                },
                            },
                        },
                    },
                }
            },
        },
        401: {
            'description': 'Não autorizado',
            'content': {
                'application/json': {
                    'examples': {
                        'not_authenticated': {
                            'summary': 'Usuário não autenticado',
                            'value': {'detail': 'Not authenticated'},
                        },
                    },
                }
            },
        },
        403: {
            'description': 'Acesso negado',
            'content': {
                'application/json': {
                    'examples': {
                        'forbidden': {
                            'summary': 'Sem permissão',
                            'value': {
                                'detail': 'You are not allowed to fetch users'
                            },
                        },
                    },
                }
            },
        },
    },
)
async def fetch_users(
    service: UserSvc,
    current_user: CurrentUser,
    offset: int = 0,
    limit: int = 100,
):
    """
    Lista usuários do sistema com paginação.
    - **Apenas administradores podem acessar.**
    - Retorna lista de usuários e informações de paginação.
    """
    await service.ensure_admin(current_user)
    users = await service.list_users(offset=offset, limit=limit)
    return await service.to_user_list(users, offset, limit)


@router.get(
    '/{user_id}',
    response_model=UserOut,
    summary='Buscar usuário por ID',
    description="""
    Retorna os dados de um usuário específico pelo seu ID. Apenas administradores podem acessar este endpoint.

    **Exemplo de requisição:**
    ```bash
    curl -X GET \
      -H "Authorization: Bearer <token>" \
      "http://localhost:8000/api/v1/users/1"
    ```
    """,  # noqa: E501
    responses={
        200: {
            'description': 'Usuário encontrado',
            'content': {
                'application/json': {
                    'examples': {
                        'async default': {
                            'summary': 'Exemplo de resposta',
                            'value': {
                                'id': '1',
                                'username': 'admin',
                                'full_name': 'Admin User',
                                'email': 'admin@example.com',
                                'role': 'admin',
                                'created_at': '2024-03-20T10:00:00',
                                'updated_at': '2024-03-20T10:00:00',
                            },
                        },
                    },
                }
            },
        },
        401: {
            'description': 'Não autorizado',
            'content': {
                'application/json': {
                    'examples': {
                        'not_authenticated': {
                            'summary': 'Usuário não autenticado',
                            'value': {'detail': 'Not authenticated'},
                        },
                    },
                }
            },
        },
        403: {
            'description': 'Acesso negado',
            'content': {
                'application/json': {
                    'examples': {
                        'forbidden': {
                            'summary': 'Sem permissão',
                            'value': {
                                'detail': 'You are not allowed to fetch users'
                            },
                        },
                    },
                }
            },
        },
        404: {
            'description': 'Usuário não encontrado',
            'content': {
                'application/json': {
                    'examples': {
                        'not_found': {
                            'summary': 'Usuário não encontrado',
                            'value': {'detail': 'User not found'},
                        },
                    },
                }
            },
        },
    },
)
async def fetch_user_by_id(
    user_id: str,
    service: UserSvc,
    current_user: CurrentUser,
):
    """
    Busca usuário pelo ID.
    - **Apenas administradores podem acessar.**
    """
    await service.ensure_admin(current_user)
    user = await service.get_user_by_id(user_id)
    return await service.to_user_out(user)


@router.post(
    '/',
    response_model=UserOut,
    status_code=HTTPStatus.CREATED,
    summary='Criar novo usuário',
    description="""
    Cria um novo usuário no sistema. Apenas administradores podem acessar este endpoint.

    **Exemplo de requisição:**
    ```bash
    curl -X POST \
      -H "Authorization: Bearer <token>" \
      -H "Content-Type: application/json" \
      -d '{"username": "newuser", "full_name": "New User", "email": "new@example.com", "password": "secure_password123", "role": "attendant"}' \
      "http://localhost:8000/api/v1/users"
    ```
    """,  # noqa: E501
    responses={
        201: {
            'description': 'Usuário criado com sucesso',
            'content': {
                'application/json': {
                    'examples': {
                        'async default': {
                            'summary': 'Exemplo de resposta',
                            'value': {
                                'id': '3',
                                'username': 'newuser',
                                'full_name': 'New User',
                                'email': 'new@example.com',
                                'role': 'attendant',
                                'created_at': '2024-03-20T10:00:00',
                                'updated_at': '2024-03-20T10:00:00',
                            },
                        },
                    },
                }
            },
        },
        400: {
            'description': 'Dados inválidos',
            'content': {
                'application/json': {
                    'examples': {
                        'invalid_email': {
                            'summary': 'Email inválido',
                            'value': {'detail': 'Invalid email format'},
                        },
                        'weak_password': {
                            'summary': 'Senha fraca',
                            'value': {'detail': 'Password is too weak'},
                        },
                    },
                }
            },
        },
        401: {
            'description': 'Não autorizado',
            'content': {
                'application/json': {
                    'examples': {
                        'not_authenticated': {
                            'summary': 'Usuário não autenticado',
                            'value': {'detail': 'Not authenticated'},
                        },
                    },
                }
            },
        },
        403: {
            'description': 'Acesso negado',
            'content': {
                'application/json': {
                    'examples': {
                        'forbidden': {
                            'summary': 'Sem permissão',
                            'value': {
                                'detail': 'You are not allowed to create users'
                            },
                        },
                    },
                }
            },
        },
        409: {
            'description': 'Conflito',
            'content': {
                'application/json': {
                    'examples': {
                        'email_conflict': {
                            'summary': 'Email já registrado',
                            'value': {'detail': 'Email already registered'},
                        },
                    },
                }
            },
        },
    },
)
async def create_user(
    dto: CreateUserDTO,
    service: UserSvc,
    current_user: CurrentUser,
):
    """
    Cria um novo usuário.
    - **Apenas administradores podem acessar.**
    - Retorna os dados do usuário criado.
    """
    await service.ensure_admin(current_user)
    user = await service.create_user(dto)
    return await service.to_user_out(user)


@router.patch('/{user_id}', response_model=UserOut)
async def update_user(
    user_id: str,
    dto: UpdateUserDTO,
    service: UserSvc,
    current_user: CurrentUser,
):
    await service.ensure_admin(current_user)
    user = await service.get_user_by_id(user_id)
    user = await service.update_user(user, dto)
    return await service.to_user_out(user)


@router.delete('/{user_id}', status_code=HTTPStatus.OK)
async def delete_user(
    user_id: str,
    service: UserSvc,
    current_user: CurrentUser,
):
    await service.ensure_admin(current_user)
    user = await service.get_user_by_id(user_id)
    await service.delete_user(user)
    return {'action': 'deleted', 'id': user_id}
