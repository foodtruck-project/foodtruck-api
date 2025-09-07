from http import HTTPStatus
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)

from projeto_aplicado.auth.security import get_current_user
from projeto_aplicado.resources.base.schemas import BaseResponse
from projeto_aplicado.resources.order.schemas import (
    CreateOrderDTO,
    OrderItemList,
    OrderList,
    OrderOut,
    UpdateOrderDTO,
)
from projeto_aplicado.resources.order.service import (
    OrderService,
    get_order_service,
)
from projeto_aplicado.resources.user.model import User
from projeto_aplicado.settings import get_settings

settings = get_settings()

OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]
router = APIRouter(tags=['Pedidos'], prefix=f'{settings.API_PREFIX}/orders')


@router.get('/', response_model=OrderList, status_code=HTTPStatus.OK)
async def fetch_orders(
    service: OrderServiceDep,
    current_user: CurrentUser,
    offset: int = 0,
    limit: int = 100,
):
    """Retorna lista paginada de pedidos."""
    orders = await service.list_orders(offset=offset, limit=limit)
    order_list = service.to_order_list(orders, offset, limit)
    return order_list


@router.get(
    '/{order_id}',
    response_model=OrderOut,
    summary='Buscar pedido por ID',
    description='Retorna dados detalhados de um pedido pelo ID.',
    responses={
        200: {'description': 'Pedido encontrado'},
        401: {'description': 'Não autenticado'},
        404: {'description': 'Pedido não encontrado'},
    },
)
async def fetch_order_by_id(
    order_id: str,
    service: OrderServiceDep,
    current_user: CurrentUser,
):
    """Busca um pedido pelo ID."""
    order = await service.get_order_by_id(order_id)
    order_out = service.to_order_out(order)
    return order_out


@router.get(
    '/{order_id}/items',
    response_model=OrderItemList,
    summary='Listar itens do pedido',
    description='Retorna lista paginada de itens de um pedido específico.',
    responses={
        200: {'description': 'Lista de itens retornada com sucesso'},
        401: {'description': 'Não autenticado'},
        404: {'description': 'Pedido não encontrado'},
    },
)
async def fetch_order_items(
    order_id: str,
    service: OrderServiceDep,
    current_user: CurrentUser,
    offset: int = 0,
    limit: int = 100,
):
    """Retorna todos os itens de um pedido."""
    order = await service.get_order_by_id(order_id)
    order_item_list = service.to_order_item_list(order, offset, limit)
    return order_item_list


@router.post('/', response_model=BaseResponse, status_code=HTTPStatus.CREATED)
async def create_order(
    dto: CreateOrderDTO,
    service: OrderServiceDep,
    current_user: CurrentUser,
):
    """Cria um novo pedido com os itens especificados."""
    order = await service.create_order(dto, current_user.role)
    response = service.to_base_response(order, 'created')
    return response


@router.patch('/{order_id}', response_model=BaseResponse)
@router.put('/{order_id}', response_model=BaseResponse)
async def update_order(
    order_id: str,
    dto: UpdateOrderDTO,
    service: OrderServiceDep,
    current_user: CurrentUser,
):
    """Atualiza ou substitui um pedido pelo ID."""
    order = await service.get_order_by_id(order_id)
    updated_order = await service.update_order(order, dto, current_user.role)
    response = service.to_base_response(updated_order, 'updated')
    return response


@router.delete(
    '/{order_id}', response_model=BaseResponse, status_code=HTTPStatus.OK
)
async def delete_order(
    order_id: str,
    service: OrderServiceDep,
    current_user: CurrentUser,
):
    """Remove um pedido pelo ID."""
    order = await service.get_order_by_id(order_id)
    await service.delete_order(order, current_user.role)
    response = service.to_base_response(order, 'deleted')
    return response
