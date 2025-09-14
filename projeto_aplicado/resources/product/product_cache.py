import json
from typing import Sequence

import redis

from projeto_aplicado.resources.product.model import Product


class ProductCache:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def product_key(self, product_id: str) -> str:
        return f'product:{product_id}'

    def list_key(self, offset: int, limit: int) -> str:
        return f'products:{offset}:{limit}'

    async def get_product_by_id(self, product_id: str):
        key = self.product_key(product_id)
        data = await self.redis.get(key)
        if not data:
            return None
        product = Product.model_validate(json.loads(data))
        return product

    async def set_product(self, product: Product, expire: int = 60):
        key = self.product_key(product.id)
        await self.redis.setex(
            key, expire, product.model_dump_json()
        )

    async def list_products(self, offset: int, limit: int) -> list[Product]:
        key = self.list_key(offset, limit)
        data = await self.redis.get(key)
        if not data:
            return []
        products = [Product.model_validate(u) for u in json.loads(data)]
        return products

    async def set_product_list(
        self,
        offset: int,
        limit: int,
        products: Sequence[Product],
        expire: int = 60,
    ):
        key = self.list_key(offset, limit)
        # Ensure datetime objects are serialized to JSON strings
        value = json.dumps([p.model_dump(mode='json') for p in products])
        await self.redis.setex(
            key,
            expire,
            value
        )

    async def invalidate_product(self, product_id: str):
        await self.redis.delete(self.product_key(product_id))

    async def invalidate_list(self):
        keys = await self.redis.keys('products:*')
        if keys:
            await self.redis.delete(*keys)

    async def invalidate_all(self):
        await self.invalidate_list()
        product_keys = await self.redis.keys('product:*')
        if product_keys:
            await self.redis.delete(*product_keys)


def get_product_cache(redis_client: redis.Redis) -> ProductCache:
    return ProductCache(redis_client=redis_client)