from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from projeto_aplicado.auth.security import get_current_user
from projeto_aplicado.resources.shared.schemas import Pagination
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
from projeto_aplicado.settings import get_settings

settings = get_settings()
UserRepo = Annotated[UserRepository, Depends(get_user_repository)]
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
                        'default': {
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
def fetch_users(
    repository: UserRepo,
    current_user: CurrentUser,
    offset: int = 0,
    limit: int = 100,
):
    """
    Lista usuários do sistema com paginação.

    - **Apenas administradores podem acessar.**
    - Retorna lista de usuários e informações de paginação.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='You are not allowed to fetch users',
        )

    users = repository.get_all(offset=offset, limit=limit)
    total_count = repository.get_total_count()
    total_pages = (total_count + limit - 1) // limit if limit > 0 else 0
    page = (offset // limit) + 1 if limit > 0 else 1
    return UserList(
        items=[
            UserOut(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
                email=user.email,
                role=user.role,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            for user in users
        ],
        pagination=Pagination(
            offset=offset,
            limit=limit,
            total_count=total_count,
            total_pages=total_pages,
            page=page,
        ),
    )


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
                        'default': {
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
def fetch_user_by_id(
    user_id: str,
    repository: UserRepo,
    current_user: CurrentUser,
):
    """
    Busca usuário pelo ID.
    - **Apenas administradores podem acessar.**
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='You are not allowed to fetch users',
        )

    user = repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )
    return UserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


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
                        'default': {
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
def create_user(
    dto: CreateUserDTO,
    repository: UserRepo,
    current_user: CurrentUser,
):
    """
    Cria um novo usuário.
    - **Apenas administradores podem acessar.**
    - Retorna os dados do usuário criado.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='You are not allowed to create users',
        )

    user = User(**dto.model_dump())
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


@router.patch('/{user_id}', response_model=UserOut)
def update_user(
    user_id: str,
    dto: UpdateUserDTO,
    repository: UserRepo,
    current_user: CurrentUser,
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='You are not allowed to update users',
        )

    user = repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )
    repository.update(user, dto.model_dump(exclude_unset=True))
    return UserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.delete('/{user_id}', status_code=HTTPStatus.OK)
def delete_user(
    user_id: str,
    repository: UserRepo,
    current_user: CurrentUser,
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='You are not allowed to delete users',
        )

    user = repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )
    repository.delete(user)
    return {'action': 'deleted', 'id': user_id}
