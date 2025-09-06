from http import HTTPStatus

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from projeto_aplicado.auth.security import get_current_user
from projeto_aplicado.resources.base.schemas import BaseResponse, Pagination
from projeto_aplicado.resources.product.model import Product
from projeto_aplicado.resources.product.repository import (
    ProductRepository,
    get_product_repository,
)
from projeto_aplicado.resources.product.schemas import (
    PRODUCT_ALREADY_EXISTS,
    PRODUCT_NOT_FOUND,
    CreateProductDTO,
    ProductList,
    ProductOut,
    UpdateProductDTO,
)
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
    product_repository: ProductRepository = Depends(get_product_repository),
):
    """
    Retorna a lista de produtos do sistema com paginação.
    """
    products = product_repository.get_all(offset=offset, limit=limit)
    total_count = product_repository.get_total_count()
    total_pages = (total_count + limit - 1) // limit if limit > 0 else 0
    page = (offset // limit) + 1 if limit > 0 else 1
    return ProductList(
        items=[
            ProductOut(
                id=product.id,
                name=product.name,
                price=product.price,
                description=product.description,
                category=product.category,
                created_at=product.created_at,
                updated_at=product.updated_at,
            )
            for product in products
        ],
        pagination=Pagination(
            offset=offset,
            limit=limit,
            total_count=total_count,
            total_pages=total_pages,
            page=page,
        ),
    )


@router.get('/{product_id}', response_model=ProductOut)
def get_product_by_id(
    product_id: str,
    current_user: User = Depends(get_current_user),
    product_repository: ProductRepository = Depends(get_product_repository),
):
    """
    Get a product by its ID.
    """
    product = product_repository.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PRODUCT_NOT_FOUND,
        )
    return ProductOut(
        id=product.id,
        name=product.name,
        price=product.price,
        description=product.description,
        category=product.category,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.post('/', response_model=BaseResponse, status_code=HTTPStatus.CREATED)
def create_product(
    product_dto: CreateProductDTO,
    product_repository: ProductRepository = Depends(get_product_repository),
    current_user: User = Depends(get_admin_user),
):
    """
    Cria um novo produto no sistema.

    Args:
        product_dto (CreateProductDTO): Dados do produto a ser criado.
        session (Session): Sessão do banco de dados.
        current_user (User): Usuário autenticado.

    Returns:
        BaseResponse: Resposta indicando o resultado da operação.

    Raises:
        HTTPException:
            - Se os dados forem inválidos (400)
            - Se o usuário não estiver autenticado (401)
            - Se o usuário não tiver permissão (403)
            - Se o produto já existir (409)

    Examples:
        ```python
        # Exemplo de requisição
        response = await client.post(
            '/api/v1/products',
            json={
                'name': 'X-Bacon',
                'description': 'Hambúrguer com bacon e queijo',
                'price': 29.90,
                'category': 'burger',
                'image_url': '[https://example.com/x-bacon.jpg](https://example.com/x-bacon.jpg)',
                'is_available': True
            },
            headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'}
        )

        # Exemplo de resposta (201 Created)
        {
            'id': '3',
            'action': 'created'
        }
        ```
    """  # noqa: E501
    existing_product = product_repository.get_by_name(product_dto.name)
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=PRODUCT_ALREADY_EXISTS,
        )
    product = Product.create(product_dto)
    product_repository.create(product)
    return BaseResponse(id=product.id, action='created')


@router.put('/{product_id}', response_model=BaseResponse)
def update_product(
    product_id: str,
    product_dto: UpdateProductDTO,
    product_repository: ProductRepository = Depends(get_product_repository),
    current_user: User = Depends(get_admin_user),
):
    """
    Update an existing product.
    """
    product = product_repository.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PRODUCT_NOT_FOUND,
        )
    updated_product = product_repository.update(
        product, product_dto.model_dump(exclude_unset=True)
    )
    return BaseResponse(id=updated_product.id, action='updated')


@router.patch('/{product_id}', response_model=BaseResponse)
def patch_product(
    product_id: str,
    product_dto: UpdateProductDTO,
    product_repository: ProductRepository = Depends(get_product_repository),
    current_user: User = Depends(get_admin_user),
):
    """
    Partially update an existing product.
    """
    product = product_repository.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PRODUCT_NOT_FOUND,
        )
    updated_product = product_repository.update(
        product, product_dto.model_dump(exclude_unset=True)
    )
    return BaseResponse(id=updated_product.id, action='updated')


@router.delete(
    '/{product_id}', response_model=BaseResponse, status_code=HTTPStatus.OK
)
def delete_product(
    product_id: str,
    product_repository: ProductRepository = Depends(get_product_repository),
    current_user: User = Depends(get_admin_user),
):
    """
    Delete a product.
    """
    product = product_repository.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PRODUCT_NOT_FOUND,
        )
    product_repository.delete(product)
    return BaseResponse(id=product_id, action='deleted')
