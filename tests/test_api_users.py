from http import HTTPStatus

import pytest

from projeto_aplicado.resources.user.model import User, UserRole
from projeto_aplicado.settings import get_settings

pytestmark = pytest.mark.asyncio

settings = get_settings()
API_PREFIX = settings.API_PREFIX


async def test_get_users(client, users: list[User], admin_headers):
    response = await client.get(f'{API_PREFIX}/users/', headers=admin_headers)
    assert response.status_code == HTTPStatus.OK
    assert response.headers['Content-Type'] == 'application/json'
    data = response.json()
    assert 'items' in data
    assert 'pagination' in data
    assert len(data['items']) == len(users)
    for user in data['items']:
        assert set(user.keys()) == {
            'id',
            'username',
            'full_name',
            'email',
            'role',
            'created_at',
            'updated_at',
        }


async def test_get_user_by_id(client, users: list[User], admin_headers):
    user_id = users[0].id
    response = await client.get(
        f'{API_PREFIX}/users/{user_id}', headers=admin_headers
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers['Content-Type'] == 'application/json'
    user = response.json()
    assert set(user.keys()) == {
        'id',
        'username',
        'full_name',
        'email',
        'role',
        'created_at',
        'updated_at',
    }
    assert user['id'] == user_id


async def test_get_user_by_id_not_found(client, admin_headers):
    response = await client.get(
        f'{API_PREFIX}/users/99999999', headers=admin_headers
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json() == {'detail': 'User not found'}


async def test_create_user(client, admin_headers):
    data = {
        'username': 'newuser',
        'full_name': 'New User',
        'email': 'newuser@example.com',
        'password': 'password123',
        'role': UserRole.KITCHEN,
    }
    response = await client.post(
        f'{API_PREFIX}/users/', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.CREATED
    user = response.json()
    assert set(user.keys()) == {
        'id',
        'username',
        'full_name',
        'email',
        'role',
        'created_at',
        'updated_at',
    }
    assert user['username'] == data['username']
    assert user['email'] == data['email']
    assert user['role'] == data['role'].value


async def test_update_user(client, users: list[User], admin_headers):
    user_id = users[0].id
    data = {
        'username': users[0].username,
        'full_name': 'Updated User',
        'email': 'updated@example.com',
        'role': UserRole.ATTENDANT,
    }
    response = await client.patch(
        f'{API_PREFIX}/users/{user_id}', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.OK
    user = response.json()
    assert set(user.keys()) == {
        'id',
        'username',
        'full_name',
        'email',
        'role',
        'created_at',
        'updated_at',
    }
    assert user['username'] == data['username']
    assert user['email'] == data['email']
    assert user['role'] == data['role'].value


async def test_update_user_not_found(client, admin_headers):
    data = {
        'username': 'Updated User',
        'email': 'updated@example.com',
        'role': UserRole.ATTENDANT,
    }
    response = await client.patch(
        f'{API_PREFIX}/users/99999999', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json() == {'detail': 'User not found'}


async def test_delete_user(client, users: list[User], admin_headers):
    user_id = users[0].id
    response = await client.delete(
        f'{API_PREFIX}/users/{user_id}', headers=admin_headers
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json() == {'action': 'deleted', 'id': user_id}


async def test_delete_user_not_found(client, admin_headers):
    response = await client.delete(
        f'{API_PREFIX}/users/99999999', headers=admin_headers
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers['Content-Type'] == 'application/json'
    assert response.json() == {'detail': 'User not found'}


async def test_kitchen_cannot_access_users_api(client, kitchen_headers):
    response = await client.get(
        f'{API_PREFIX}/users/', headers=kitchen_headers
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


async def test_attendant_cannot_access_users_api(client, attendant_headers):
    response = await client.get(
        f'{API_PREFIX}/users/', headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


async def test_get_users_unauthorized(client, users: list[User]):
    response = await client.get(f'{API_PREFIX}/users/')
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_get_users_invalid_token(client, users: list[User]):
    response = await client.get(
        f'{API_PREFIX}/users/',
        headers={'Authorization': 'Bearer invalid_token'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_create_user_with_invalid_email(client, admin_headers):
    data = {
        'username': 'newuser',
        'full_name': 'New User',
        'email': 'invalid-email',
        'password': 'password123',
        'role': UserRole.KITCHEN,
    }
    response = await client.post(
        f'{API_PREFIX}/users/', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_create_user_with_short_password(client, admin_headers):
    data = {
        'username': 'newuser',
        'full_name': 'New User',
        'email': 'newuser@example.com',
        'password': '12345',  # Too short
        'role': UserRole.KITCHEN,
    }
    response = await client.post(
        f'{API_PREFIX}/users/', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_create_user_with_invalid_role(client, admin_headers):
    data = {
        'username': 'newuser',
        'full_name': 'New User',
        'email': 'newuser@example.com',
        'password': 'password123',
        'role': 'INVALID_ROLE',
    }
    response = await client.post(
        f'{API_PREFIX}/users/', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_create_user_with_missing_required_fields(client, admin_headers):
    data = {
        'username': 'newuser',
        'full_name': 'New User',
        'email': 'newuser@example.com',
        # Missing password and role
    }
    response = await client.post(
        f'{API_PREFIX}/users/', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_update_user_with_invalid_email(
    client, users: list[User], admin_headers
):
    data = {
        'username': users[0].username,
        'full_name': 'Updated User',
        'email': 'invalid-email',
        'role': UserRole.ATTENDANT,
    }
    response = await client.patch(
        f'{API_PREFIX}/users/{users[0].id}', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_update_user_with_invalid_role(
    client, users: list[User], admin_headers
):
    data = {
        'username': users[0].username,
        'full_name': 'Updated User',
        'email': 'updated@example.com',
        'role': 'INVALID_ROLE',
    }
    response = await client.patch(
        f'{API_PREFIX}/users/{users[0].id}', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_update_user_with_short_password(
    client, users: list[User], admin_headers
):
    data = {
        'username': users[0].username,
        'full_name': 'Updated User',
        'email': 'updated@example.com',
        'password': '12345',  # Too short
        'role': UserRole.ATTENDANT,
    }
    response = await client.patch(
        f'{API_PREFIX}/users/{users[0].id}', json=data, headers=admin_headers
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_kitchen_cannot_create_user(client, kitchen_headers):
    data = {
        'username': 'newuser',
        'full_name': 'New User',
        'email': 'newuser@example.com',
        'password': 'password123',
        'role': UserRole.KITCHEN,
    }
    response = await client.post(
        f'{API_PREFIX}/users/', json=data, headers=kitchen_headers
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


async def test_attendant_cannot_create_user(client, attendant_headers):
    data = {
        'username': 'newuser',
        'full_name': 'New User',
        'email': 'newuser@example.com',
        'password': 'password123',
        'role': UserRole.KITCHEN,
    }
    response = await client.post(
        f'{API_PREFIX}/users/', json=data, headers=attendant_headers
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
