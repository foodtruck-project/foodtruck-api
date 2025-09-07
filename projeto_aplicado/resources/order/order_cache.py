import json
from typing import Sequence

import redis

from projeto_aplicado.resources.order.model import Order


class OrderCache:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def order_key(self, order_id: str) -> str:
        return f'order:{order_id}'

    def list_key(self, offset: int, limit: int) -> str:
        return f'orders:{offset}:{limit}'

    async def get_order_by_id(self, order_id: str):
        key = self.order_key(order_id)
        data = await self.redis.get(key)
        if not data:
            return None
        order = Order.model_validate(json.loads(data))
        return order

    async def set_order(self, order: Order, expire: int = 60):
        key = self.order_key(order.id)
        await self.redis.setex(key, expire, order.model_dump_json())

    async def list_orders(self, offset: int, limit: int) -> list[Order]:
        key = self.list_key(offset, limit)
        data = await self.redis.get(key)
        if not data:
            return []
        orders = [Order.model_validate(u) for u in json.loads(data)]
        return orders

    async def set_order_list(
        self,
        offset: int,
        limit: int,
        orders: Sequence[Order],
        expire: int = 60,
    ):
        key = self.list_key(offset, limit)
        await self.redis.setex(
            key,
            expire,
            json.dumps([json.loads(u.model_dump_json()) for u in orders]),
        )

    async def invalidate_order(self, order_id: str):
        await self.redis.delete(self.order_key(order_id))

    async def invalidate_list(self):
        keys = await self.redis.keys('orders:*')
        if keys:
            await self.redis.delete(*keys)

    async def invalidate_all(self):
        await self.invalidate_list()
        order_keys = await self.redis.keys('order:*')
        if order_keys:
            await self.redis.delete(*order_keys)


def get_order_cache(redis_client: redis.Redis) -> OrderCache:
    return OrderCache(redis_client=redis_client)
