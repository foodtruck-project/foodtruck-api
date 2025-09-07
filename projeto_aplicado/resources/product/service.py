from http import HTTPStatus
from typing import Sequence

from fastapi import Depends, HTTPException

from projeto_aplicado.ext.cache.redis import get_redis
from projeto_aplicado.resources.base.schemas import BaseResponse, Pagination
from projeto_aplicado.resources.product.model import Product
from projeto_aplicado.resources.product.product_cache import (
    ProductCache,
    get_product_cache,
)
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


class ProductService:
    def __init__(
        self, repository: ProductRepository, product_cache: ProductCache
    ):
        self.repository = repository
        self.product_cache = product_cache

    async def list_products(
        self, offset: int, limit: int
    ) -> Sequence[Product]:
        cached_products = await self.product_cache.list_products(offset, limit)
        if cached_products:
            return cached_products
        products = self.repository.get_all(offset=offset, limit=limit)
        await self.product_cache.set_product_list(offset, limit, products)
        return products

    async def get_product_by_id(self, product_id: str) -> Product:
        cached_product = await self.product_cache.get_product_by_id(product_id)
        if cached_product:
            return cached_product
        product = self.repository.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=PRODUCT_NOT_FOUND
            )
        await self.product_cache.set_product(product)
        return product

    async def create_product(self, dto: CreateProductDTO) -> Product:
        existing = self.repository.get_by_name(dto.name)
        if existing:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail=PRODUCT_ALREADY_EXISTS
            )
        product = Product.create(dto)
        await self.product_cache.invalidate_list()
        await self.product_cache.invalidate_product(product.id)
        created = self.repository.create(product)
        return created

    async def update_product(
        self, product: Product, dto: UpdateProductDTO
    ) -> Product:
        updated = self.repository.update(
            product, dto.model_dump(exclude_unset=True)
        )
        await self.product_cache.invalidate_product(product.id)
        await self.product_cache.invalidate_list()
        return updated

    async def delete_product(self, product: Product) -> None:
        self.repository.delete(product)
        await self.product_cache.invalidate_product(product.id)
        await self.product_cache.invalidate_list()

    async def to_product_out(self, product: Product) -> ProductOut:
        return ProductOut(
            id=product.id,
            name=product.name,
            price=product.price,
            description=product.description,
            category=product.category,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    async def to_product_list(
        self, products: Sequence[Product], offset: int, limit: int
    ) -> ProductList:
        return ProductList(
            items=[await self.to_product_out(product) for product in products],
            pagination=await self.get_pagination(offset, limit),
        )

    async def to_base_response(
        self, product: Product, action: str
    ) -> BaseResponse:
        return BaseResponse(id=product.id, action=action)

    async def get_pagination(
        self,
        offset: int,
        limit: int,
        total_count: int = 0,
        total_pages: int = 0,
        page: int = 1,
    ) -> Pagination:
        return Pagination(
            offset=offset,
            limit=limit,
            total_count=total_count,
            total_pages=total_pages,
            page=page,
        )


async def get_product_service(
    repo: ProductRepository = Depends(get_product_repository),
    redis=Depends(get_redis),
):
    product_cache = get_product_cache(redis)
    return ProductService(repo, product_cache)
