from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, func, select

from projeto_aplicado.ext.database.db import get_session
from projeto_aplicado.resources.base.repository import BaseRepository
from projeto_aplicado.resources.order.model import Order, OrderItem
from projeto_aplicado.resources.order.schemas import (
    PublicProductData,
)


def get_order_repository(session: Annotated[Session, Depends(get_session)]):
    return OrderRepository(session)


class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: Session):
        super().__init__(session, Order)

    def get_total_count(self) -> int:
        stmt = select(func.count()).select_from(Order)
        return self.session.exec(stmt).one()

    def get_all(self, offset: int = 0, limit: int = 100) -> list[Order]:
        return list(super().get_all(offset=offset, limit=limit))

    def update(self, entity: Order, update_data: dict) -> Order:
        return super().update(entity, update_data)

    def get_all_public(self) -> list[PublicProductData]:
        """
        Retorna uma lista de todos os produtos com suas quantidades e ratings, de todos os pedidos.
        Esta é uma consulta otimizada que une as tabelas Order e OrderItem.
        """  # noqa: E501
        stmt = select(
            OrderItem.product_id,
            OrderItem.quantity,
            Order.rating,
        ).where(Order.rating is not None)

        results = self.session.exec(stmt).all()

        return [
            PublicProductData(
                product_id=row[0],
                quantity=row[1],
                rating=row[2],
            )
            for row in results
        ]
