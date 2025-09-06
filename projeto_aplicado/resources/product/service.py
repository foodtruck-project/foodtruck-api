from http import HTTPStatus
from typing import Sequence

from fastapi import HTTPException

from projeto_aplicado.resources.base.schemas import BaseResponse, Pagination
from projeto_aplicado.resources.product.model import Product
from projeto_aplicado.resources.product.repository import ProductRepository
from projeto_aplicado.resources.product.schemas import (
    PRODUCT_ALREADY_EXISTS,
    PRODUCT_NOT_FOUND,
    CreateProductDTO,
    ProductList,
    ProductOut,
    UpdateProductDTO,
)


class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def list_products(self, offset: int, limit: int) -> Sequence[Product]:
        return self.repository.get_all(offset=offset, limit=limit)

    def get_product_by_id(self, product_id: str) -> Product:
        product = self.repository.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=PRODUCT_NOT_FOUND
            )
        return product

    def create_product(self, dto: CreateProductDTO) -> Product:
        existing = self.repository.get_by_name(dto.name)
        if existing:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail=PRODUCT_ALREADY_EXISTS
            )
        product = Product.create(dto)
        return self.repository.create(product)

    def update_product(
        self, product: Product, dto: UpdateProductDTO
    ) -> Product:
        return self.repository.update(
            product, dto.model_dump(exclude_unset=True)
        )

    def delete_product(self, product: Product) -> None:
        self.repository.delete(product)

    def to_product_out(self, product: Product) -> ProductOut:
        return ProductOut(
            id=product.id,
            name=product.name,
            price=product.price,
            description=product.description,
            category=product.category,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    def to_product_list(
        self, products: Sequence[Product], offset: int, limit: int
    ) -> ProductList:
        return ProductList(
            items=[self.to_product_out(product) for product in products],
            pagination=self.get_pagination(offset, limit),
        )

    def to_base_response(self, product: Product, action: str) -> BaseResponse:
        return BaseResponse(id=product.id, action=action)

    def get_pagination(
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
