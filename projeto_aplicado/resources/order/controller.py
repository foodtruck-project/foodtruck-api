from http import HTTPStatus
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)

from projeto_aplicado.auth.security import get_current_user
from projeto_aplicado.resources.base.schemas import BaseResponse
from projeto_aplicado.resources.order.repository import (
    OrderRepository,
    get_order_repository,
)
from projeto_aplicado.resources.order.schemas import (
    CreateOrderDTO,
    OrderItemList,
    OrderList,
    OrderOut,
    UpdateOrderDTO,
)
from projeto_aplicado.resources.order.service import OrderService
from projeto_aplicado.resources.product.repository import (
    ProductRepository,
    get_product_repository,
)
from projeto_aplicado.resources.user.model import User
from projeto_aplicado.settings import get_settings

settings = get_settings()


OrderRepo = Annotated[OrderRepository, Depends(get_order_repository)]
ProductRepo = Annotated[ProductRepository, Depends(get_product_repository)]


def get_order_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    product_repo: ProductRepository = Depends(get_product_repository),
) -> OrderService:
    return OrderService(order_repo, product_repo)


OrderSvc = Annotated[OrderService, Depends(get_order_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]
router = APIRouter(tags=['Pedidos'], prefix=f'{settings.API_PREFIX}/orders')


@router.get(
    '/',
    response_model=OrderList,
    status_code=HTTPStatus.OK,
    responses={
        200: {
            'description': 'Lista de pedidos retornada com sucesso',
            'content': {
                'application/json': {
                    'example': {
                        'orders': [
                            {
                                'id': '1',
                                'status': 'pending',
                                'total': 41.80,
                                'created_at': '2024-03-20T10:00:00',
                                'updated_at': '2024-03-20T10:00:00',
                                'locator': 'A123',
                                'notes': 'Sem cebola',
                            },
                            {
                                'id': '2',
                                'status': 'preparing',
                                'total': 25.90,
                                'created_at': '2024-03-20T10:00:00',
                                'updated_at': '2024-03-20T10:00:00',
                                'locator': 'B456',
                                'notes': None,
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
def fetch_orders(
    service: OrderSvc,
    current_user: CurrentUser,
    offset: int = 0,
    limit: int = 100,
):
    """
    Retorna a lista de pedidos do sistema.
    """
    orders = service.list_orders(offset=offset, limit=limit)
    return service.to_order_list(orders, offset, limit)


@router.get('/{order_id}', response_model=OrderOut)
def fetch_order_by_id(
    order_id: str,
    service: OrderSvc,
    current_user: CurrentUser,
):
    """
    Get a order by ID.
    """
    order = service.get_order_by_id(order_id)
    return service.to_order_out(order)


@router.get('/{order_id}/items', response_model=OrderItemList)
def fetch_order_items(
    order_id: str,
    service: OrderSvc,
    current_user: CurrentUser,
    offset: int = 0,
    limit: int = 100,
):
    """
    Get all items of an order.
    """
    order = service.get_order_by_id(order_id)
    return service.to_order_item_list(order, offset, limit)


@router.post(
    '/',
    response_model=BaseResponse,
    status_code=HTTPStatus.CREATED,
    responses={
        201: {
            'description': 'Pedido criado com sucesso',
            'content': {
                'application/json': {
                    'example': {
                        'id': '3',
                        'action': 'created',
                    }
                }
            },
        },
        400: {
            'description': 'Dados inválidos',
            'content': {
                'application/json': {
                    'examples': {
                        'empty_items': {
                            'value': {
                                'detail': 'Order must have at least one item'
                            },
                            'summary': 'Lista de itens vazia',
                        },
                        'invalid_quantity': {
                            'value': {
                                'detail': 'Quantity must be greater than zero'
                            },
                            'summary': 'Quantidade inválida',
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
        403: {
            'description': 'Acesso negado',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'You are not allowed to create orders',
                    }
                }
            },
        },
        422: {
            'description': 'Entidade não processável',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'Product not found',
                    }
                }
            },
        },
    },
)
async def create_order(
    dto: CreateOrderDTO,
    service: OrderSvc,
    current_user: CurrentUser,
):
    """
    Cria um novo pedido no sistema.
    """
    order = service.create_order(dto, current_user.role)
    return service.to_base_response(order, 'created')


@router.patch('/{order_id}', response_model=BaseResponse)
def update_order(
    order_id: str,
    dto: UpdateOrderDTO,
    service: OrderSvc,
    current_user: CurrentUser,
):
    """
    Update an order by ID.
    """
    order = service.get_order_by_id(order_id)
    updated_order = service.update_order(order, dto, current_user.role)
    return service.to_base_response(updated_order, 'updated')


@router.delete('/{order_id}', response_model=BaseResponse)
def delete_order(
    order_id: str,
    service: OrderSvc,
    current_user: CurrentUser,
):
    """
    Delete an order by ID.
    """
    order = service.get_order_by_id(order_id)
    service.delete_order(order, current_user.role)
    return service.to_base_response(order, 'deleted')
