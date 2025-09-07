from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from projeto_aplicado.ext.database.db import get_session
from projeto_aplicado.resources.product.model import Product
from projeto_aplicado.resources.product.repository import ProductRepository
from projeto_aplicado.resources.product.schemas import PublicProduct
from projeto_aplicado.settings import get_settings

settings = get_settings()

router = APIRouter(
    tags=['Public Products'], prefix=f'{settings.API_PREFIX}/public/products'
)


@router.get('/', response_model=List[PublicProduct], status_code=HTTPStatus.OK)
def fetch_public_products(session: Session = Depends(get_session)):
    """
    Retorna a lista de produtos disponíveis publicamente.
    """
    repository = ProductRepository(model=Product, session=session)
    return repository.get_all_public()
