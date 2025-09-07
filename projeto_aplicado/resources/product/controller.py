from http import HTTPStatus
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)

from projeto_aplicado.auth.security import get_current_user
from projeto_aplicado.resources.base.schemas import BaseResponse
from projeto_aplicado.resources.product.schemas import (
    CreateProductDTO,
    ProductList,
    ProductOut,
    UpdateProductDTO,
)
from projeto_aplicado.resources.product.service import (
    ProductService,
    get_product_service,
)
from projeto_aplicado.resources.user.controller import UserService
from projeto_aplicado.resources.user.model import User
from projeto_aplicado.resources.user.service import get_user_service
from projeto_aplicado.settings import get_settings

settings = get_settings()

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(tags=['Produtos'], prefix=f'{settings.API_PREFIX}/products')


@router.get(
    '/',
    response_model=ProductList,
    status_code=HTTPStatus.OK,
    responses={
        200: {
            'description': 'Lista de produtos retornada com sucesso',
            'content': {
                'application/json': {
                    'example': {
                        'items': [
                            {
                                'id': '1',
                                'name': 'X-Burger',
                                'description': 'Hambúrguer artesanal com queijo',  # noqa: E501
                                'price': 25.90,
                                'category': 'burger',
                                'image_url': 'https://example.com/x-burger.jpg',
                                'is_available': True,
                                'created_at': '2024-03-20T10:00:00',
                                'updated_at': '2024-03-20T10:00:00',
                            },
                            {
                                'id': '2',
                                'name': 'Batata Frita',
                                'description': 'Porção de batata frita crocante',  # noqa: E501
                                'price': 15.90,
                                'category': 'side',
                                'image_url': 'https://example.com/fries.jpg',
                                'is_available': True,
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
                    }
                }
            },
        },
        401: {
            'description': 'Não autorizado',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'Not authenticated',
                    }
                }
            },
        },
    },
)
async def fetch_products(
    current_user: CurrentUser,
    service: ProductServiceDep,
    offset: int = 0,
    limit: int = 100,
):
    """
    Retorna a lista de produtos do sistema com paginação.
    """

    products = await service.list_products(offset=offset, limit=limit)
    product_list = await service.to_product_list(products, offset, limit)
    return product_list


@router.get('/{product_id}', response_model=ProductOut)
async def get_product_by_id(
    product_id: str,
    current_user: CurrentUser,
    service: ProductServiceDep,
):
    """
    Get a product by its ID.
    """
    product = await service.get_product_by_id(product_id)
    product_out = await service.to_product_out(product)
    return product_out


@router.post('/', response_model=BaseResponse, status_code=HTTPStatus.CREATED)
async def create_product(
    product_dto: CreateProductDTO,
    user_service: UserServiceDep,
    current_user: CurrentUser,
    service: ProductServiceDep,
):
    """
    Cria um novo produto no sistema.
    """
    await user_service.ensure_admin(current_user)
    product = await service.create_product(product_dto)
    response = await service.to_base_response(product, 'created')
    return response


@router.put('/{product_id}', response_model=BaseResponse)
async def update_product(
    product_id: str,
    product_dto: UpdateProductDTO,
    user_service: UserServiceDep,
    current_user: CurrentUser,
    service: ProductServiceDep,
):
    """
    Update an existing product.
    """
    await user_service.ensure_admin(current_user)
    product = await service.get_product_by_id(product_id)
    updated_product = await service.update_product(product, product_dto)
    response = await service.to_base_response(updated_product, 'updated')
    return response


@router.delete(
    '/{product_id}', response_model=BaseResponse, status_code=HTTPStatus.OK
)
async def delete_product(
    product_id: str,
    user_service: UserServiceDep,
    current_user: CurrentUser,
    service: ProductServiceDep,
):
    """
    Delete a product.
    """
    await user_service.ensure_admin(current_user)
    product = await service.get_product_by_id(product_id)
    await service.delete_product(product)
    response = await service.to_base_response(product, 'deleted')
    return response
