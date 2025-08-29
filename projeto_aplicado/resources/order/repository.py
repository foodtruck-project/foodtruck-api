from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, func, select

from projeto_aplicado.ext.database.db import get_session
from projeto_aplicado.resources.order.model import Order, OrderItem
from projeto_aplicado.resources.order.schemas import (
    PublicProductData,
    UpdateOrderDTO,
)
from projeto_aplicado.resources.shared.repository import BaseRepository


def get_order_repository(session: Annotated[Session, Depends(get_session)]):
    return OrderRepository(session)


class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: Session):
        super().__init__(session, Order)

    def get_total_count(self) -> int:
        stmt = select(func.count()).select_from(Order)
        return self.session.exec(stmt).one()

    def get_all(self, offset: int = 0, limit: int = 100) -> list[Order]:
        return super().get_all(offset=offset, limit=limit)

    def update(self, order: Order, dto: UpdateOrderDTO) -> Order:
        update_data = dto.model_dump(exclude_unset=True)
        return super().update(order, update_data)

    def get_all_public(self) -> list[PublicProductData]:
        """
        Retorna uma lista de todos os produtos com suas quantidades e ratings, de todos os pedidos.
        Esta é uma consulta otimizada que une as tabelas Order e OrderItem.
        """
        stmt = (
            select(
                OrderItem.product_id,
                OrderItem.quantity,
                Order.rating,
            )
            .join(Order)
            .where(Order.rating.isnot(None))
        )

        results = self.session.exec(stmt).all()

        return [
            PublicProductData(
                product_id=row.product_id,
                quantity=row.quantity,
                rating=row.rating,
            )
            for row in results
        ]
