# 🚀 Sistema de Gerenciamento de Food Truck

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![uv](https://img.shields.io/badge/package%20manager-uv-orange.svg)](https://github.com/astral-sh/uv)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

> **Sistema completo de gerenciamento para food trucks com API REST e interface web**

## 📋 Visão Geral

O Sistema de Gerenciamento de Food Truck é uma aplicação completa construída em **FastAPI** que oferece:

- 🚀 **API REST de Alto Desempenho** - Construída em ASGI com suporte a async/await
- 📖 **Documentação Interativa** - Documentação automática OpenAPI/Swagger
- 🔒 **Segurança JWT** - Autenticação com controle de acesso baseado em funções

- 🗄️ **Banco PostgreSQL** - Persistência robusta com migrações Alembic
- 🐳 **Docker Ready** - Containerização completa para implantação

## 🏗️ Arquitetura

### Padrões Arquiteturais
- **Arquitetura em Camadas**: Separação clara entre apresentação, negócio e dados
- **Padrão Repository**: Abstração de acesso a dados
- **Design Orientado a Domínio**: Lógica organizada em entidades de domínio
- **Influências da Arquitetura Limpa**: Inversão de dependência

### Estrutura do Projeto
```
projeto_aplicado/
├── app.py                    # 🚀 Ponto de entrada FastAPI
├── settings.py               # ⚙️  Configuração
├── auth/                     # 🔐 Autenticação JWT
├── ext/                      # 🔌 Integrações (DB, Cache)
└── resources/               # 🏢 Domínios (User, Product, Order)
    ├── user/                #     Gerenciamento de usuários
    ├── product/             #     Catálogo de produtos
    ├── order/               #     Pedidos e workflow
    └── shared/              #     Componentes compartilhados
```

## 🚀 Instalação Rápida

### Pré-requisitos
- **Docker** - Para executar todos os serviços

### Início Rápido com Docker Compose
```bash
# Clonar e configurar tudo automaticamente
git clone https://github.com/foodtruck-project/foodtruck-api.git
cd foodtruck-api
docker-compose up --build -d

# Inicializar container de modo interativo
docker-compose up

# Inicializar container de  modo "detached" (ou background)
docker-compose up -d

# Migrações de banco de dados no Windows
docker-compose exec backend uv run alembic upgrade head
```
**Cria o primeiro usuário (administrador)**:
```bash
curl -X 'POST' \
  'http://foodtruck.docker.localhost/api/v1/users/setup' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "role": "admin",
  "full_name": "admin"
}'
```
## 🔌 API REST

### Informações da API

| Propriedade | Valor |
|-------------|-------|
| **URL Base** | `http://localhost:8000` | `http://foodtruck.docker.localhost/` |
| **Versão** | v1 |
| **Prefixo** | `/api/v1` |
| **Documentação** | `/docs` (Swagger UI) |
| **ReDoc** | `/redoc` |

### Autenticação
A API usa **JWT (JSON Web Tokens)** para autenticação.

**Obter Token**:
```bash
curl -X POST "http://localhost:8000/api/v1/token/" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin@foodtruck.com&password=admin123"
```

**Usar Token**:
```bash
curl -H "Authorization: Bearer <seu-token>" \
     http://localhost:8000/api/v1/users
```

### Endpoints Principais

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| **🔐 Autenticação** | | | |
| `POST` | `/api/v1/token/` | Login e obtenção de token JWT | Público |
| **👥 Usuários** | | | |
| `GET` | `/api/v1/users/` | Listar usuários | Admin |
| `GET` | `/api/v1/users/{user_id}` | Obter usuário específico | Admin |
| `POST` | `/api/v1/users/` | Criar usuário | Admin |
| **🍔 Produtos** | | | |
| `GET` | `/api/v1/products/` | Listar produtos | Público |
| `GET` | `/api/v1/products/{product_id}` | Obter produto específico | Público |
| `POST` | `/api/v1/products/` | Criar produto | Admin |
| `PUT` | `/api/v1/products/{product_id}` | Atualizar produto | Admin |
| `DELETE` | `/api/v1/products/{product_id}` | Deletar produto | Admin |
| **📋 Pedidos** | | | |
| `GET` | `/api/v1/orders/` | Listar pedidos | Autenticado |
| `GET` | `/api/v1/orders/{order_id}` | Obter pedido específico | Autenticado |
| `POST` | `/api/v1/orders/` | Criar pedido | Autenticado |
| `PUT` | `/api/v1/orders/{order_id}` | Atualizar pedido | Autenticado |
| `DELETE` | `/api/v1/orders/{order_id}` | Deletar pedido | Autenticado |



## 🗄️ Banco de Dados

### Entidades Principais
```sql
Users (1) ────────── (N) Orders
               │
Orders (1) ─────── (N) OrderItems  
               │
OrderItems (N) ── (1) Products
```

### Características
- **SQLModel ORM**: Operações type-safe
- **Chaves Primárias ULID**: Identificadores únicos e ordenáveis
- **Migrações Alembic**: Controle de versão do banco
- **Connection Pooling**: Gerenciado automaticamente

## 🧪 Testes

```bash
# Executar todos os testes
uv run pytest

# Executar testes com cobertura
uv run pytest --cov=projeto_aplicado

# Executar testes específicos
uv run pytest tests/test_api_users.py
```

## 🔧 Desenvolvimento

### Estrutura de Testes
```
tests/
├── conftest.py              # Configuração de testes
├── test_api_users.py        # Testes da API de usuários
├── test_api_products.py     # Testes da API de produtos
├── test_api_order.py        # Testes da API de pedidos
└── test_auth/               # Testes de autenticação
    ├── test_token_api.py    # Testes da API de token
    └── test_token_unit.py   # Testes unitários de token
```

### Comandos de Desenvolvimento
```bash
# Instalar dependências de desenvolvimento
uv sync --group dev --group test

# Executar linting
uv run task lint

# Executar formatação
uv run task format

# Executar type checking
uv run mypy projeto_aplicado/
```

### Comandos de Migração
```bash
# Aplicar todas as migrações pendentes
uv run task migrate

# Criar nova migração (substitua "descrição" pela descrição da migração)
uv run task migrate-create "descrição da migração"

# Ver histórico de migrações
uv run task migrate-history

# Ver migração atual
uv run task migrate-current

# Fazer downgrade da última migração
uv run task migrate-downgrade

# Fazer upgrade para próxima migração
uv run task migrate-upgrade

# Marcar banco como atualizado (sem aplicar migrações)
uv run task migrate-stamp
```

## 🚀 Implantação

### Docker
```bash
# Construir imagem
docker build -t foodtruck-api .

# Executar container
docker run -p 8000:8000 foodtruck-api
```

### Docker Compose (Recomendado)
```bash
# Iniciar todos os serviços
docker-compose up --build -d

# Verificar logs
docker-compose logs -f api

# Parar serviços
docker-compose down
```

## 📚 Recursos Externos

### 🛠️ Ferramentas e Frameworks

| Ferramenta | Descrição | Link |
|------------|-----------|------|
| **FastAPI** | Framework web moderno e rápido | [Documentação](https://fastapi.tiangolo.com/) |
| **SQLModel** | ORM moderno baseado em Pydantic | [Documentação](https://sqlmodel.tiangolo.com/) |
| **uv** | Gerenciador de pacotes Python rápido | [Documentação](https://github.com/astral-sh/uv) |

### 🎓 Recursos de Aprendizado

| Tópico | Descrição | Link |
|--------|-----------|------|
| **Arquitetura Limpa** | Princípios de design de software | [Artigo](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) |
| **Princípios SOLID** | Princípios de design orientado a objetos | [Wikipedia](https://en.wikipedia.org/wiki/SOLID) |
| **Type Hints Python** | Sistema de tipos do Python | [Documentação](https://docs.python.org/3/library/typing.html) |
| **Docker Best Practices** | Melhores práticas para containers | [Documentação](https://docs.docker.com/develop/dev-best-practices/) |

## 🐛 Suporte

- **🐛 Reportar Problemas**: [GitHub Issues](https://github.com/foodtruck-project/foodtruck-api/issues)
- **💡 Sugerir Melhorias**: [GitHub Issues](https://github.com/foodtruck-project/foodtruck-api/issues)

---

<div align="center">

**📖 Sistema de Gerenciamento de Food Truck - Documentação Completa**

[🏠 Projeto Principal](https://github.com/foodtruck-project/foodtruck-api) • [🚀 Começar Agora](#-instalação-rápida)

</div>
