from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, func, select

from projeto_aplicado.ext.database.db import get_session
from projeto_aplicado.resources.base.repository import BaseRepository
from projeto_aplicado.resources.product.model import Product
from projeto_aplicado.resources.product.schemas import PublicProduct


def get_product_repository(session: Annotated[Session, Depends(get_session)]):
    return ProductRepository(model=Product, session=session)


class ProductRepository(BaseRepository[Product]):
    def __init__(self, model: type[Product], session: Session):
        super().__init__(model=model, session=session)

    def get_total_count(self) -> int:
        stmt = select(func.count()).select_from(Product)
        return self.session.exec(stmt).one()

    def get_all_public(self) -> list[PublicProduct]:
        """
        Retorna uma lista de todos os produtos apenas com os campos públicos.
        """
        stmt = select(Product)
        products = self.session.exec(stmt).all()
        return [PublicProduct.model_validate(p) for p in products]

    def get_by_name(self, name: str) -> Product | None:
        stmt = select(Product).where(Product.name == name)
        return self.session.exec(stmt).first()
