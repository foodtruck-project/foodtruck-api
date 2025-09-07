import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, StaticPool, create_engine
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from projeto_aplicado.app import app
from projeto_aplicado.auth.password import get_password_hash
from projeto_aplicado.ext.cache.redis import get_redis
from projeto_aplicado.ext.database.db import get_session
from projeto_aplicado.resources.order.model import Order, OrderItem
from projeto_aplicado.resources.product.enums import ProductCategory
from projeto_aplicado.resources.product.model import Product
from projeto_aplicado.resources.user.model import User, UserRole
from projeto_aplicado.settings import get_settings
from projeto_aplicado.utils import create_all, drop_all

settings = get_settings()


@pytest.fixture(scope='session')
def postgres_container():
    """Start the Postgres test container."""
    container = PostgresContainer(
        'postgres:16',
        username=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB,
        driver='psycopg2',
    )
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope='session')
def redis_client():
    """Get the Redis client from the container."""
    with RedisContainer() as redis_container:
        yield redis_container.get_client()


@pytest.fixture(scope='session')
def engine(postgres_container):
    engine = create_engine(
        postgres_container.get_connection_url(),
        echo=settings.DB_ECHO,
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture
def session(engine):
    create_all(engine)  # noqa: F821

    with Session(engine) as session:
        yield session

    drop_all(engine)


@pytest_asyncio.fixture
async def client(session, redis_client):
    def get_session_override():
        return session

    def get_redis_override():
        return redis_client

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as client:
        app.dependency_overrides[get_session] = get_session_override
        app.dependency_overrides[get_redis] = get_redis_override
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def itens(session):
    itens = [
        {
            'name': 'X-Burguer',
            'price': 25.0,
            'image_url': 'image_x_burguer.jpg',
            'category': ProductCategory.FOOD,
        },
        {
            'name': 'X-Salada',
            'price': 20.0,
            'image_url': 'image_x_salada.jpg',
            'category': ProductCategory.FOOD,
        },
        {
            'name': 'Cachorro-quente',
            'price': 10.0,
            'image_url': 'image_cachorro_quente.jpg',
            'category': ProductCategory.FOOD,
        },
        {
            'name': 'Refrigerante',
            'price': 5.0,
            'image_url': 'image_refrigerante.jpg',
            'category': ProductCategory.DRINK,
        },
        {
            'name': 'Batata frita',
            'price': 8.0,
            'image_url': 'image_batata_frita.jpg',
            'category': ProductCategory.SNACK,
        },
        {
            'name': 'Pudim',
            'price': 12.0,
            'image_url': 'image_pudim.jpg',
            'category': ProductCategory.DESSERT,
        },
    ]

    itens = [
        Product(
            name=item['name'],
            price=item['price'],
            category=item['category'],
        )
        for item in itens
    ]
    session.add_all(itens)
    session.commit()
    return itens


@pytest.fixture
def products(itens):
    return itens


@pytest.fixture
def orders(session):
    orders = [
        {
            'status': 'pending',
            'total': 0.0,
            'notes': 'First order',
            'rating': 3,
        },
        {
            'status': 'completed',
            'total': 0.0,
            'notes': 'Second order',
            'rating': 4,
        },
        {
            'status': 'cancelled',
            'total': 0.0,
            'notes': 'Third order',
            'rating': 5,
        },
    ]
    orders = [Order(**order) for order in orders]
    session.add_all(orders)
    session.commit()
    return orders


@pytest.fixture
def order_items(session, orders, itens):
    order_items = [
        {
            'order_id': orders[0].id,
            'product_id': itens[0].id,
            'quantity': 2,
            'price': itens[0].price,
        },
        {
            'order_id': orders[0].id,
            'product_id': itens[2].id,
            'quantity': 1,
            'price': itens[2].price,
        },
        {
            'order_id': orders[1].id,
            'product_id': itens[1].id,
            'quantity': 3,
            'price': itens[1].price,
        },
    ]
    order_items = [OrderItem(**item) for item in order_items]
    session.add_all(order_items)
    session.commit()
    return order_items


@pytest.fixture
def users(session):
    users = [
        {
            'username': 'johndoe',
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'password': get_password_hash('password'),
            'role': UserRole.ATTENDANT,
        },
        {
            'username': 'janedoe',
            'name': 'Jane Doe',
            'email': 'jane.doe@example.com',
            'password': get_password_hash('password'),
            'role': UserRole.KITCHEN,
        },
        {
            'username': 'admin',
            'name': 'Admin',
            'email': 'admin@example.com',
            'password': get_password_hash('password'),
            'role': UserRole.ADMIN,
        },
    ]
    users = [User(**user) for user in users]
    session.add_all(users)
    session.commit()
    return users


@pytest_asyncio.fixture
async def admin_headers(client, users):
    response = await client.post(
        f'{settings.API_PREFIX}/token/',
        data={'username': users[2].username, 'password': 'password'},
    )
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    return headers


@pytest_asyncio.fixture
async def kitchen_headers(client, users):
    response = await client.post(
        f'{settings.API_PREFIX}/token/',
        data={'username': users[1].username, 'password': 'password'},
    )
    headers = {'Authorization': f'Bearer {response.json()["access_token"]}'}
    return headers


@pytest_asyncio.fixture
async def attendant_headers(client, users):
    response = await client.post(
        f'{settings.API_PREFIX}/token/',
        data={'username': users[0].username, 'password': 'password'},
    )
    headers = {'Authorization': f'Bearer {response.json()["access_token"]}'}
    return headers
