from datetime import datetime
from http import HTTPStatus

from projeto_aplicado.resources.order.enums import OrderStatus
from projeto_aplicado.settings import get_settings

settings = get_settings()
API_PREFIX = settings.API_PREFIX


def test_get_orders(client, orders, admin_headers):
    response = client.get(f'{API_PREFIX}/orders/', headers=admin_headers)
    assert response.status_code == HTTPStatus.OK
    assert response.headers['Content-Type'] == 'application/json'
    assert len(response.json()['orders']) == len(orders)
    # Comparar apenas campos essenciais, ignorando diferenças de serialização
    api_orders = response.json()['orders']
    expected_orders = [
        {
            'id': order.id,
            'status': order.status.upper(),
            'total': order.total,
            'created_at': order.created_at.replace(tzinfo=None).isoformat(),
            'updated_at': order.updated_at.replace(tzinfo=None).isoformat(),
            'locator': order.locator,
            'products': [],
            'notes': order.notes,
            'rating': order.rating,
        }
        for order in orders
    ]
    for api_order, expected in zip(api_orders, expected_orders):
        # Normaliza datas removendo timezone para comparação
        api_order_norm = dict(api_order)
        # Remove qualquer timezone (+HH:MM ou -HH:MM) para comparar só a data/hora
        for dt_field in ['created_at', 'updated_at']:
            dt_val = api_order_norm[dt_field]
            if '+' in dt_val:
                api_order_norm[dt_field] = dt_val.split('+')[0]
            elif '-' in dt_val[10:]:  # ignora o '-' da data
                # timezone negativo só aparece depois do décimo caractere (YYYY-MM-DDTHH:MM:SS)
                idx = dt_val.find('-', 10)
                api_order_norm[dt_field] = dt_val[:idx]
            else:
                api_order_norm[dt_field] = dt_val
        # Compara apenas os campos esperados
        for key in expected:
            assert api_order_norm[key] == expected[key], (
                f"Campo '{key}' diferente: esperado={expected[key]} recebido={api_order_norm[key]}"
            )
    assert response.json()['pagination'] == {
        'offset': 0,
        'limit': 100,
        'total_count': len(orders),
        'page': 1,
        'total_pages': 1,
    }


def test_get_order_by_id(client, orders, order_items, admin_headers):
    response = client.get(
        f'{API_PREFIX}/orders/{orders[0].id}', headers=admin_headers
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json()['products']
    api_order = response.json()
    expected_order = {
        'id': orders[0].id,
        'status': orders[0].status.upper(),
        'total': orders[0].total,
        'created_at': orders[0].created_at.isoformat(),
        'updated_at': orders[0].updated_at.isoformat(),
        'locator': orders[0].locator,
        'notes': orders[0].notes,
        'rating': orders[0].rating,
        'products': [
            {
                'id': order_items[0].id,
                'quantity': order_items[0].quantity,
                'price': order_items[0].price,
                'product_id': order_items[0].product_id,
                'order_id': order_items[0].order_id,
            },
            {
                'id': order_items[1].id,
                'quantity': order_items[1].quantity,
                'price': order_items[1].price,
                'product_id': order_items[1].product_id,
                'order_id': order_items[1].order_id,
            },
        ],
    }
    # Normaliza datas removendo timezone
    for dt_field in ['created_at', 'updated_at']:
        dt_val = api_order[dt_field]
        if '+' in dt_val:
            api_order[dt_field] = dt_val.split('+')[0]
        elif '-' in dt_val[10:]:
            idx = dt_val.find('-', 10)
            api_order[dt_field] = dt_val[:idx]
        else:
            api_order[dt_field] = dt_val
        # Remove timezone do esperado também, para garantir
        exp_val = expected_order[dt_field]
        if '+' in exp_val:
            expected_order[dt_field] = exp_val.split('+')[0]
        elif '-' in exp_val[10:]:
            idx = exp_val.find('-', 10)
            expected_order[dt_field] = exp_val[:idx]
        else:
            expected_order[dt_field] = exp_val
    assert api_order == expected_order


def test_get_order_by_id_not_found(client, admin_headers):
    response = client.get(
        f'{API_PREFIX}/orders/99999999', headers=admin_headers
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json() == {'detail': 'Order not found'}


def test_create_order(client, itens, attendant_headers):
    data = {
        'items': [
            {
                'product_id': itens[0].id,
                'quantity': 2,
                'price': itens[0].price,
            },
            {
                'product_id': itens[1].id,
                'quantity': 3,
                'price': itens[1].price,
            },
        ],
        'notes': 'Test order',
    }
    response = client.post(
        f'{API_PREFIX}/orders/', json=data, headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json()['action'] == 'created'

    order_response = client.get(
        f'{API_PREFIX}/orders/{response.json()["id"]}',
        headers=attendant_headers,
    )
    assert order_response.status_code == HTTPStatus.OK

    expected_total = (itens[0].price * 2) + (itens[1].price * 3)
    assert order_response.json()['total'] == expected_total


def test_create_order_single_item(client, itens, attendant_headers):
    data = {
        'items': [
            {
                'product_id': itens[0].id,
                'quantity': 1,
                'price': itens[0].price,
            }
        ],
        'notes': 'Test order with single item',
    }
    response = client.post(
        f'{API_PREFIX}/orders/', json=data, headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.CREATED

    order_response = client.get(
        f'{API_PREFIX}/orders/{response.json()["id"]}',
        headers=attendant_headers,
    )
    assert order_response.status_code == HTTPStatus.OK

    assert order_response.json()['total'] == itens[0].price


def test_update_order(client, orders, attendant_headers):
    data = {
        'status': 'COMPLETED',
        'notes': 'Updated order',
    }
    response = client.patch(
        f'{API_PREFIX}/orders/{orders[0].id}',
        json=data,
        headers=attendant_headers,
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json()['action'] == 'updated'


def test_update_order_not_found(client, attendant_headers):
    data = {
        'status': 'COMPLETED',
        'notes': 'Updated order',
    }
    response = client.patch(
        f'{API_PREFIX}/orders/99999999', json=data, headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json() == {'detail': 'Order not found'}


def test_delete_order(client, orders, attendant_headers):
    # Ensure the order is pending before deletion
    data = {
        'status': 'PENDING',
        'notes': orders[0].notes,
    }
    client.patch(
        f'{API_PREFIX}/orders/{orders[0].id}',
        json=data,
        headers=attendant_headers,
    )
    response = client.delete(
        f'{API_PREFIX}/orders/{orders[0].id}', headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json()['action'] == 'deleted'


def test_delete_order_not_found(client, attendant_headers):
    response = client.delete(
        f'{API_PREFIX}/orders/1', headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json() == {'detail': 'Order not found'}


def test_create_order_with_empty_items(client, attendant_headers):
    data = {
        'items': [],
        'notes': 'Empty order',
    }
    response = client.post(
        f'{API_PREFIX}/orders/', json=data, headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_order_with_zero_quantity(client, attendant_headers):
    data = {
        'items': [
            {
                'product_id': '1',
                'quantity': 0,
                'price': 10.0,
            }
        ],
    }
    response = client.post(
        f'{API_PREFIX}/orders/', json=data, headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_order_with_negative_price(client, attendant_headers):
    data = {
        'items': [
            {
                'product_id': '1',
                'quantity': 1,
                'price': -10.0,
            }
        ],
    }
    response = client.post(
        f'{API_PREFIX}/orders/', json=data, headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_update_order_created_at_unchanged(client, orders, attendant_headers):
    # Get initial created_at
    initial_response = client.get(
        f'{API_PREFIX}/orders/{orders[0].id}', headers=attendant_headers
    )
    initial_created_at = datetime.fromisoformat(
        initial_response.json()['created_at']
    )

    # Update the order
    data = {
        'status': OrderStatus.COMPLETED,
        'notes': 'Updated order',
    }
    response = client.patch(
        f'{API_PREFIX}/orders/{orders[0].id}',
        json=data,
        headers=attendant_headers,
    )
    assert response.status_code == HTTPStatus.OK

    # Verify created_at remains unchanged
    updated_response = client.get(
        f'{API_PREFIX}/orders/{orders[0].id}', headers=attendant_headers
    )
    updated_created_at = datetime.fromisoformat(
        updated_response.json()['created_at']
    )
    assert updated_created_at == initial_created_at


def test_update_order_updated_at_changes(client, orders, attendant_headers):
    # Get initial updated_at
    initial_response = client.get(
        f'{API_PREFIX}/orders/{orders[0].id}', headers=attendant_headers
    )
    initial_updated_at = datetime.fromisoformat(
        initial_response.json()['updated_at']
    )

    # Update the order
    data = {
        'status': OrderStatus.COMPLETED,
        'notes': 'Updated order',
    }
    response = client.patch(
        f'{API_PREFIX}/orders/{orders[0].id}',
        json=data,
        headers=attendant_headers,
    )
    assert response.status_code == HTTPStatus.OK

    # Verify updated_at changes
    updated_response = client.get(
        f'{API_PREFIX}/orders/{orders[0].id}', headers=attendant_headers
    )
    updated_updated_at = datetime.fromisoformat(
        updated_response.json()['updated_at']
    )
    assert updated_updated_at > initial_updated_at


def test_order_total_with_large_quantity(client, itens, attendant_headers):
    data = {
        'items': [
            {
                'product_id': itens[0].id,
                'quantity': 1000,
                'price': itens[0].price,
            }
        ],
        'notes': 'Large quantity order',
    }
    response = client.post(
        f'{API_PREFIX}/orders/', json=data, headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.CREATED

    order_response = client.get(
        f'{API_PREFIX}/orders/{response.json()["id"]}',
        headers=attendant_headers,
    )
    assert order_response.status_code == HTTPStatus.OK

    expected_total = itens[0].price * 1000
    assert order_response.json()['total'] == expected_total


def test_order_total_with_small_price(client, itens, attendant_headers):
    data = {
        'items': [
            {
                'product_id': itens[0].id,
                'quantity': 1,
                'price': 0.01,
            }
        ],
        'notes': 'Small price order',
    }
    response = client.post(
        f'{API_PREFIX}/orders/', json=data, headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.CREATED

    order_response = client.get(
        f'{API_PREFIX}/orders/{response.json()["id"]}',
        headers=attendant_headers,
    )
    assert order_response.status_code == HTTPStatus.OK

    expected_total = 0.01
    assert order_response.json()['total'] == expected_total


def test_order_status_transition_to_pending(client, orders, attendant_headers):
    data = {
        'status': OrderStatus.PENDING,
        'notes': 'Transition to pending',
    }
    response = client.patch(
        f'{API_PREFIX}/orders/{orders[0].id}',
        json=data,
        headers=attendant_headers,
    )
    assert response.status_code == HTTPStatus.OK


def test_order_status_transition_to_completed(
    client, orders, attendant_headers
):
    data = {
        'status': OrderStatus.COMPLETED,
        'notes': 'Transition to completed',
    }
    response = client.patch(
        f'{API_PREFIX}/orders/{orders[0].id}',
        json=data,
        headers=attendant_headers,
    )
    assert response.status_code == HTTPStatus.OK


def test_order_status_transition_to_cancelled(
    client, orders, attendant_headers
):
    data = {
        'status': OrderStatus.CANCELLED,
        'notes': 'Transition to cancelled',
    }
    response = client.patch(
        f'{API_PREFIX}/orders/{orders[0].id}',
        json=data,
        headers=attendant_headers,
    )
    assert response.status_code == HTTPStatus.OK


def test_order_status_transition_to_invalid_status(
    client, orders, attendant_headers
):
    data = {
        'status': 'INVALID_STATUS',
        'notes': 'Invalid status transition',
    }
    response = client.patch(
        f'{API_PREFIX}/orders/{orders[0].id}',
        json=data,
        headers=attendant_headers,
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_order_locator_not_empty(client, itens, attendant_headers):
    data = {
        'items': [
            {
                'product_id': itens[0].id,
                'quantity': 1,
                'price': itens[0].price,
            }
        ],
        'notes': 'Order with locator',
    }
    response = client.post(
        f'{API_PREFIX}/orders/', json=data, headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.CREATED

    order_response = client.get(
        f'{API_PREFIX}/orders/{response.json()["id"]}',
        headers=attendant_headers,
    )
    assert order_response.status_code == HTTPStatus.OK
    assert order_response.json()['locator'] is not None


def test_order_locator_unique(client, itens, attendant_headers):
    # Create first order
    data1 = {
        'items': [
            {
                'product_id': itens[0].id,
                'quantity': 1,
                'price': itens[0].price,
            }
        ],
        'notes': 'First order',
    }
    response1 = client.post(
        f'{API_PREFIX}/orders/', json=data1, headers=attendant_headers
    )
    assert response1.status_code == HTTPStatus.CREATED

    # Create second order
    data2 = {
        'items': [
            {
                'product_id': itens[1].id,
                'quantity': 1,
                'price': itens[1].price,
            }
        ],
        'notes': 'Second order',
    }
    response2 = client.post(
        f'{API_PREFIX}/orders/', json=data2, headers=attendant_headers
    )
    assert response2.status_code == HTTPStatus.CREATED

    # Verify locators are unique
    order1_response = client.get(
        f'{API_PREFIX}/orders/{response1.json()["id"]}',
        headers=attendant_headers,
    )
    order2_response = client.get(
        f'{API_PREFIX}/orders/{response2.json()["id"]}',
        headers=attendant_headers,
    )
    assert (
        order1_response.json()['locator'] != order2_response.json()['locator']
    )


def test_get_orders_unauthorized(client, orders):
    response = client.get(f'{API_PREFIX}/orders/')
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_orders_invalid_token(client, orders):
    response = client.get(
        f'{API_PREFIX}/orders/',
        headers={'Authorization': 'Bearer invalid_token'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_kitchen_cannot_create_order(client, itens, kitchen_headers):
    data = {
        'items': [
            {
                'product_id': itens[0].id,
                'quantity': 1,
                'price': itens[0].price,
            }
        ],
        'notes': 'Test order',
    }
    response = client.post(
        f'{API_PREFIX}/orders/', json=data, headers=kitchen_headers
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_kitchen_can_update_order(client, orders, kitchen_headers):
    data = {
        'status': 'COMPLETED',
        'notes': 'Updated by kitchen',
    }
    response = client.patch(
        f'{API_PREFIX}/orders/{orders[0].id}',
        json=data,
        headers=kitchen_headers,
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json()['action'] == 'updated'

    # Verify the order was actually updated
    get_response = client.get(
        f'{API_PREFIX}/orders/{orders[0].id}',
        headers=kitchen_headers,
    )
    assert get_response.status_code == HTTPStatus.OK
    assert get_response.json()['status'] == 'COMPLETED'
    assert get_response.json()['notes'] == 'Updated by kitchen'


def test_kitchen_cannot_delete_order(client, orders, kitchen_headers):
    response = client.delete(
        f'{API_PREFIX}/orders/{orders[0].id}', headers=kitchen_headers
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_create_order_with_invalid_product_id(client, attendant_headers):
    data = {
        'items': [
            {
                'product_id': 'invalid_id',
                'quantity': 1,
                'price': 10.0,
            }
        ],
        'notes': 'Test order',
    }
    response = client.post(
        f'{API_PREFIX}/orders/', json=data, headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_order_with_missing_required_fields(client, attendant_headers):
    data = {
        'items': [
            {
                'product_id': '1',
                'quantity': 1,
            }
        ],
    }
    response = client.post(
        f'{API_PREFIX}/orders/', json=data, headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_update_order_with_invalid_status(client, orders, attendant_headers):
    data = {
        'status': 'INVALID_STATUS',
        'notes': 'Invalid status',
    }
    response = client.patch(
        f'{API_PREFIX}/orders/{orders[0].id}',
        json=data,
        headers=attendant_headers,
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_update_order_with_invalid_data_type(
    client, orders, attendant_headers
):
    data = {
        'status': 123,  # Should be string
        'notes': 'Invalid data type',
    }
    response = client.patch(
        f'{API_PREFIX}/orders/{orders[0].id}',
        json=data,
        headers=attendant_headers,
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
