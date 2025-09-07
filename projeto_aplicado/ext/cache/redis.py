from redis.asyncio import Redis as AsyncRedis

from projeto_aplicado.settings import get_settings


def redis_factory(
    host: str | None = None,
    port: int | None = None,
    db: int = 0,
    password: str | None = None,
    decode_responses: bool = True,
    **kwargs,
) -> AsyncRedis:
    """
    Factory to create an async Redis client with settings fallback.
    """
    settings = get_settings()
    return AsyncRedis(
        host=host or settings.REDIS_HOSTNAME,
        port=port or settings.REDIS_PORT,
        db=db,
        password=password,
        decode_responses=decode_responses,
        **kwargs,
    )


redis = redis_factory()


def get_redis() -> AsyncRedis:
    """
    Dependency for FastAPI DI: returns the default async Redis client.
    """
    return redis
