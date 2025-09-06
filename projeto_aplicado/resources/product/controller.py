from http import HTTPStatus

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from projeto_aplicado.auth.security import get_current_user
from projeto_aplicado.resources.base.schemas import BaseResponse
from projeto_aplicado.resources.product.repository import (
    ProductRepository,
    get_product_repository,
)
from projeto_aplicado.resources.product.schemas import (
    CreateProductDTO,
    ProductList,
    ProductOut,
    UpdateProductDTO,
)
from projeto_aplicado.resources.product.service import ProductService
from projeto_aplicado.resources.user.model import User, UserRole
from projeto_aplicado.settings import get_settings

settings = get_settings()

router = APIRouter(tags=['Produtos'], prefix=f'{settings.API_PREFIX}/products')


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only admin users can perform this action',
        )
    return current_user


def get_user_service(
    repo: ProductRepository = Depends(get_product_repository),
) -> ProductService:
    return ProductService(repo)


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
def fetch_products(
    offset: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    service: ProductService = Depends(get_user_service),
):
    """
    Retorna a lista de produtos do sistema com paginação.
    """
    products = service.list_products(offset=offset, limit=limit)
    return service.to_product_list(products, offset, limit)


@router.get('/{product_id}', response_model=ProductOut)
def get_product_by_id(
    product_id: str,
    current_user: User = Depends(get_current_user),
    service: ProductService = Depends(get_user_service),
):
    """
    Get a product by its ID.
    """
    product = service.get_product_by_id(product_id)
    return service.to_product_out(product)


@router.post('/', response_model=BaseResponse, status_code=HTTPStatus.CREATED)
def create_product(
    product_dto: CreateProductDTO,
    service: ProductService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user),
):
    """
    Cria um novo produto no sistema.
    """
    product = service.create_product(product_dto)
    return service.to_base_response(product, 'created')


@router.put('/{product_id}', response_model=BaseResponse)
def update_product(
    product_id: str,
    product_dto: UpdateProductDTO,
    service: ProductService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user),
):
    """
    Update an existing product.
    """
    product = service.get_product_by_id(product_id)
    updated_product = service.update_product(product, product_dto)
    return service.to_base_response(updated_product, 'updated')


@router.patch('/{product_id}', response_model=BaseResponse)
def patch_product(
    product_id: str,
    product_dto: UpdateProductDTO,
    service: ProductService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user),
):
    """
    Partially update an existing product.
    """
    product = service.get_product_by_id(product_id)
    updated_product = service.update_product(product, product_dto)
    return service.to_base_response(updated_product, 'updated')


@router.delete(
    '/{product_id}', response_model=BaseResponse, status_code=HTTPStatus.OK
)
def delete_product(
    product_id: str,
    service: ProductService = Depends(get_user_service),
    current_user: User = Depends(get_admin_user),
):
    """
    Delete a product.
    """
    product = service.get_product_by_id(product_id)
    service.delete_product(product)
    return service.to_base_response(product, 'deleted')
