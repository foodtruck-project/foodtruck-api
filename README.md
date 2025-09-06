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

```bash
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

# Migrações de banco de dados no Windows
docker-compose exec backend uv run alembic upgrade head
```

### Criar o primeiro usuário (administrador)

```bash
curl -X 'POST' \
  'http://foodtruck.docker.localhost/api/v1/users/setup' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "foodtruck-admin",
  "email": "admin@foodtruck.com",
  "password": "admin123456",
  "role": "admin",
  "full_name": "Admin da Silva"
}'
```

## 🔌 API REST

### Informações da API

| Propriedade | Valor |
|-------------|-------|
| **URL Base** | `http://foodtruck.docker.localhost/` |
| **Versão** | v1 |
| **Prefixo** | `/api/v1` |
| **Swagger** | [Swagger UI](http://foodtruck.docker.localhost/docs) |

### Autenticação

A API usa **JWT (JSON Web Tokens)** para autenticação.

**Obter Token**:

```bash
curl -X POST "http://foodtruck.docker.localhost/api/v1/token/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=foodtruck-admin&password=admin123456"
```

**Usar Token**:

```bash
curl -H "Authorization: Bearer <seu-token>" \
  http://foodtruck.docker.localhost/api/v1/users
```

## 🧪 Testes

```bash
uv run task test
```
