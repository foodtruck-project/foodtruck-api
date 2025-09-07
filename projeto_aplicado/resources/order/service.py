from http import HTTPStatus
from typing import Sequence
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException

from projeto_aplicado.ext.cache.redis import get_redis
from projeto_aplicado.resources.base.schemas import BaseResponse, Pagination
from projeto_aplicado.resources.order.enums import OrderStatus
from projeto_aplicado.resources.order.model import Order, OrderItem
from projeto_aplicado.resources.order.order_cache import (
    OrderCache,
    get_order_cache,
)
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
from projeto_aplicado.resources.product.repository import (
    ProductRepository,
    get_product_repository,
)
from projeto_aplicado.resources.user.model import UserRole


class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        product_repository: ProductRepository,
        order_cache: OrderCache,
    ):
        self.repository = repository
        self.product_repository = product_repository
        self.order_cache = order_cache

    async def list_orders(self, offset: int, limit: int) -> Sequence[Order]:
        cached_orders = await self.order_cache.list_orders(offset, limit)
        if cached_orders:
            return cached_orders
        products = self.repository.get_all(offset=offset, limit=limit)
        await self.order_cache.set_order_list(offset, limit, products)
        return products

    async def get_order_by_id(self, order_id: str) -> Order:
        cached_order = await self.order_cache.get_order_by_id(order_id)
        if cached_order:
            return cached_order

        order = self.repository.get_by_id(order_id)
        if not order:
            await self.order_cache.invalidate_order(order_id)
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='Order not found'
            )
        return order

    async def create_order(
        self, dto: CreateOrderDTO, current_user_role: str
    ) -> Order:
        if current_user_role not in {UserRole.ADMIN, UserRole.ATTENDANT}:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='You are not allowed to create orders',
            )
        new_order = Order.create(dto)
        for item in dto.items:
            product = self.product_repository.get_by_id(item.product_id)
            if not product:
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                    detail='Product not found',
                )
            order_item = OrderItem.create(item)
            new_order.products.append(order_item)
        new_order.total = sum(
            item.calculate_total() for item in new_order.products
        )
        await self.order_cache.invalidate_order(new_order.id)
        await self.order_cache.invalidate_list()
        created_order = self.repository.create(new_order)
        return created_order

    async def update_order(
        self, order: Order, dto: UpdateOrderDTO, current_user_role: str
    ) -> Order:
        if current_user_role not in {
            UserRole.ADMIN,
            UserRole.ATTENDANT,
            UserRole.KITCHEN,
        }:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='You are not allowed to update orders',
            )
        updated = self.repository.update(
            order, dto.model_dump(exclude_unset=True)
        )
        await self.order_cache.invalidate_order(order.id)
        await self.order_cache.invalidate_list()
        return updated

    async def delete_order(self, order: Order, current_user_role: str) -> None:
        if current_user_role not in {UserRole.ADMIN, UserRole.ATTENDANT}:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='You are not allowed to delete orders',
            )
        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Order is not pending',
            )
        self.repository.delete(order)
        await self.order_cache.invalidate_order(order.id)
        await self.order_cache.invalidate_list()

    def to_order_out(self, order: Order) -> OrderOut:
        return OrderOut(
            id=order.id,
            status=OrderStatus(order.status.upper()),
            total=order.total,
            created_at=order.created_at.astimezone(
                ZoneInfo('America/Sao_Paulo')
            ).isoformat(),
            updated_at=order.updated_at.astimezone(
                ZoneInfo('America/Sao_Paulo')
            ).isoformat(),
            locator=order.locator,
            products=order.products,  # type: ignore
            notes=order.notes,
            rating=order.rating,
        )

    def to_order_list(
        self, orders: Sequence[Order], offset: int, limit: int
    ) -> OrderList:
        return OrderList(
            orders=[self.to_order_out(order) for order in orders],
            pagination=self.get_pagination(offset, limit),
        )

    def to_order_item_list(
        self, order: Order, offset: int, limit: int
    ) -> OrderItemList:
        return OrderItemList(
            order_items=order.products,
            pagination=self.get_pagination(offset, limit),
        )

    def get_pagination(self, offset: int, limit: int) -> Pagination:
        total_count = self.repository.get_total_count()
        total_pages = (total_count + limit - 1) // limit if limit else 1
        page = (offset // limit) + 1 if limit else 1
        return Pagination(
            offset=offset,
            limit=limit,
            total_count=total_count,
            total_pages=total_pages,
            page=page,
        )

    def to_base_response(self, order: Order, action: str) -> BaseResponse:
        return BaseResponse(id=order.id, action=action)


async def get_order_service(
    repo: OrderRepository = Depends(get_order_repository),
    product_repo: ProductRepository = Depends(get_product_repository),
    redis=Depends(get_redis),
):
    order_cache = get_order_cache(redis)
    return OrderService(repo, product_repo, order_cache)
