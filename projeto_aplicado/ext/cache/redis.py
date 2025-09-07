from redis import Redis

from projeto_aplicado.settings import get_settings

settings = get_settings()

redis = Redis(
    host=settings.REDIS_HOSTNAME,
    port=settings.REDIS_PORT,
    decode_responses=True,
)


def get_redis():
    return redis.client()
