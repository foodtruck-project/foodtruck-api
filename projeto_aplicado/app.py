from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine

from projeto_aplicado.auth.security import get_current_user
from projeto_aplicado.auth.token import router as token_router
from projeto_aplicado.ext.database.db import get_engine
from projeto_aplicado.middleware.security import SecurityHeadersMiddleware
from projeto_aplicado.resources.order.controller import router as order_router
from projeto_aplicado.resources.product.controller import router as item_router
from projeto_aplicado.resources.public.order.controller import (
    router as public_order_router,
)
from projeto_aplicado.resources.public.products.controller import (
    router as public_products_router,
)
from projeto_aplicado.resources.setup.controller import router as setup_router
from projeto_aplicado.resources.user.controller import router as user_router
from projeto_aplicado.resources.user.model import User
from projeto_aplicado.settings import get_settings

settings = get_settings()
engine: Engine = get_engine()

CurrentUser = Annotated[User, Depends(get_current_user)]

app = FastAPI(
    title='Food Truck API',
    version=settings.API_VERSION,
    description="""
    API do sistema de gerenciamento de FoodTruck desenvolvido para o Projeto Aplicado do SENAI 2025.

    ## Funcionalidades

    * 🔐 **Autenticação**: Sistema de login com JWT
    * 👥 **Usuários**: Gerenciamento de usuários e perfis
    * 🍔 **Produtos**: Cadastro e gerenciamento de produtos
    * 🛍️ **Pedidos**: Sistema completo de pedidos

    ## Documentação

    * `/docs`: Interface Swagger para testes interativos
    * `/redoc`: Documentação ReDoc mais detalhada
    """,  # noqa: E501
    servers=[
        {
            "url": "https://api-foodtruck.bentomachado.dev",
            "description": "Production server"
        },
        {
            "url": "http://localhost:8080",
            "description": "Development server"
        }
    ],
    openapi_tags=[
        {
            'name': 'Token',
            'description': 'Operações de autenticação e geração de tokens JWT',
        },
        {
            'name': 'Usuários',
            'description': 'Gerenciamento de usuários e perfis do sistema',
        },
        {
            'name': 'Produtos',
            'description': 'Operações relacionadas ao cadastro e gerenciamento de produtos',  # noqa: E501
        },
        {
            'name': 'Pedidos',
            'description': 'Sistema de pedidos e gerenciamento de comandas',
        },
        {
            'name': 'Public Products',
            'description': 'Operações públicas relacionadas a produtos',
        },
        {
            'name': 'Public Orders',
            'description': 'Operações públicas relacionadas a pedidos',
        },
        {
            'name': 'Setup',
            'description': 'Operações de configuração inicial do sistema',
        },
    ],
)

# Add permissive CORS - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Cannot be True when allow_origins is "*"
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Add minimal security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(token_router)
app.include_router(user_router)
app.include_router(item_router)
app.include_router(order_router)
app.include_router(public_products_router)
app.include_router(public_order_router)
app.include_router(setup_router)


@app.get('/health', tags=['Health'], include_in_schema=False)
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {'status': 'healthy', 'service': 'foodtruck-api'}
