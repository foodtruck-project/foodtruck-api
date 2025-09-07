from http import HTTPStatus

import pytest

from projeto_aplicado.resources.product.enums import ProductCategory
from projeto_aplicado.resources.product.model import Product
from projeto_aplicado.settings import get_settings

pytestmark = pytest.mark.asyncio
settings = get_settings()
API_PREFIX = settings.API_PREFIX


async def test_get_products(client, itens, admin_headers):
    response = await client.get(
        f'{API_PREFIX}/products/', headers=admin_headers
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers['Content-Type'] == 'application/json'
    data = response.json()
    assert 'items' in data
    assert len(data['items']) == len(itens)
    for product in data['items']:
        assert set(product.keys()) == {
            'id',
            'description',
            'name',
            'price',
            'category',
            'created_at',
            'updated_at',
        }


async def test_get_product_by_id_not_found(client, admin_headers):
    response = await client.get(
        f'{API_PREFIX}/products/nonexistent-id', headers=admin_headers
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json()['detail'] == 'Product not found'


async def test_create_product(client, admin_headers):
    data = {
        'name': 'Test Item',
        'description': 'Test Description',
        'price': 10.99,
        'category': 'FOOD',
    }
    response = await client.post(
        f'{API_PREFIX}/products/', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.CREATED
    product = response.json()
    assert set(product.keys()) == {'action', 'id'}
    assert product['action'] == 'created'
    assert product['id'] is not None


async def test_create_product_conflict(client, itens, admin_headers):
    data = {
        'name': itens[0].name,
        'description': 'Test Description',
        'price': 10.99,
        'category': itens[0].category.value,
    }
    response = await client.post(
        f'{API_PREFIX}/products/',
        json=data,
        headers=admin_headers,
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json()['detail'] == 'Product already exists'


async def test_update_product(client, itens, admin_headers):
    payload = {'name': 'Updated Item', 'price': 1599.99}
    response = await client.patch(
        f'{API_PREFIX}/products/{itens[0].id}',
        json=payload,
        headers=admin_headers,
    )
    assert response.status_code == HTTPStatus.OK
    product = response.json()
    assert set(product.keys()) == {'action', 'id'}
    assert product['action'] == 'updated'
    assert product['id'] == itens[0].id


async def test_update_product_not_found(client, admin_headers):
    update_payload = {'name': 'Nonexistent Item', 'price': 20.99}
    response = await client.patch(
        f'{API_PREFIX}/products/nonexistent-id',
        json=update_payload,
        headers=admin_headers,
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json()['detail'] == 'Product not found'


async def test_delete_product(client, itens, admin_headers):
    response = await client.delete(
        f'{API_PREFIX}/products/{itens[0].id}', headers=admin_headers
    )
    assert response.status_code == HTTPStatus.OK
    product = response.json()
    assert set(product.keys()) == {'action', 'id'}
    assert product['action'] == 'deleted'
    assert product['id'] == itens[0].id


async def test_delete_product_not_found(client, admin_headers):
    response = await client.delete(
        f'{API_PREFIX}/products/nonexistent-id', headers=admin_headers
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json()['detail'] == 'Product not found'


async def test_kitchen_cannot_access_products_api(client, kitchen_headers):
    response = await client.get(
        f'{API_PREFIX}/products/', headers=kitchen_headers
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers['Content-Type'] == 'application/json'


async def test_attendant_cannot_access_products_api(client, attendant_headers):
    response = await client.get(
        f'{API_PREFIX}/products/', headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers['Content-Type'] == 'application/json'


async def test_get_products_unauthorized(client, products: list[Product]):
    response = await client.get(f'{API_PREFIX}/products/')
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_get_products_invalid_token(client, products: list[Product]):
    response = await client.get(
        f'{API_PREFIX}/products/',
        headers={'Authorization': 'Bearer invalid_token'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_create_product_with_invalid_price(client, admin_headers):
    data = {
        'name': 'New Product',
        'description': 'A new product',
        'price': -10.0,  # Invalid negative price
        'category': ProductCategory.FOOD,
    }
    response = await client.post(
        f'{API_PREFIX}/products/', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_create_product_with_invalid_category(client, admin_headers):
    data = {
        'name': 'New Product',
        'description': 'A new product',
        'price': 10.0,
        'category': 'INVALID_CATEGORY',
    }
    response = await client.post(
        f'{API_PREFIX}/products/', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_create_product_with_missing_required_fields(
    client, admin_headers
):
    data = {
        'name': 'New Product',
        # Missing description, price, and category
    }
    response = await client.post(
        f'{API_PREFIX}/products/', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_update_product_with_invalid_price(
    client, products: list[Product], admin_headers
):
    data = {
        'name': 'Updated Product',
        'description': 'An updated product',
        'price': -5.0,  # Invalid negative price
        'category': ProductCategory.DRINK,
    }
    response = await client.patch(
        f'{API_PREFIX}/products/{products[0].id}',
        json=data,
        headers=admin_headers,
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_update_product_with_invalid_category(
    client, products: list[Product], admin_headers
):
    data = {
        'name': 'Updated Product',
        'description': 'An updated product',
        'price': 5.0,
        'category': 'INVALID_CATEGORY',
    }
    response = await client.patch(
        f'{API_PREFIX}/products/{products[0].id}',
        json=data,
        headers=admin_headers,
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_kitchen_cannot_create_product(client, kitchen_headers):
    data = {
        'name': 'New Product',
        'description': 'A new product',
        'price': 10.0,
        'category': ProductCategory.FOOD,
    }
    response = await client.post(
        f'{API_PREFIX}/products/', json=data, headers=kitchen_headers
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


async def test_attendant_cannot_create_product(client, attendant_headers):
    data = {
        'name': 'New Product',
        'description': 'A new product',
        'price': 10.0,
        'category': ProductCategory.FOOD,
    }
    response = await client.post(
        f'{API_PREFIX}/products/', json=data, headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
