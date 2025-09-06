from http import HTTPStatus
from typing import List, Annotated

from fastapi import APIRouter, Depends

from projeto_aplicado.resources.order.repository import (
    OrderRepository,
    get_order_repository,
)
from projeto_aplicado.resources.order.schemas import PublicProductData
from projeto_aplicado.settings import get_settings

settings = get_settings()

OrderRepo = Annotated[OrderRepository, Depends(get_order_repository)]

router = APIRouter(tags=['Public Orders'], prefix=f'{settings.API_PREFIX}/public/orders')

@router.get('/', response_model=List[PublicProductData], status_code=HTTPStatus.OK)
def fetch_public_orders(repository: OrderRepo):
    """
    Retorna dados públicos de avaliações de produtos de todos os pedidos.
    """
    return repository.get_all_public()
