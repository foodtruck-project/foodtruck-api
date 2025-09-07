import json
from typing import Sequence

import redis

from projeto_aplicado.resources.user.model import User


class UserCache:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def user_key(self, user_id: str) -> str:
        return f'user:{user_id}'

    def list_key(self, offset: int, limit: int) -> str:
        return f'users:{offset}:{limit}'

    async def get_user_by_id(self, user_id: str, expire: int = 60):
        key = self.user_key(user_id)
        data = await self.redis.get(key)
        if not data:
            return None
        user = User.model_validate(json.loads(data))
        return user

    async def set_user(self, user: User, expire: int = 60):
        key = self.user_key(user.id)
        await self.redis.setex(key, expire, json.dumps(user.model_dump_json()))

    async def list_users(self, offset: int, limit: int) -> list[User]:
        key = self.list_key(offset, limit)
        data = await self.redis.get(key)
        if not data:
            return []
        users = [User.model_validate(u) for u in json.loads(data)]
        return users

    async def set_user_list(
        self, offset: int, limit: int, users: Sequence[User], expire: int = 60
    ):
        key = self.list_key(offset, limit)
        await self.redis.setex(
            key, expire, json.dumps([u.model_dump_json() for u in users])
        )

    async def invalidate_user(self, user_id: str):
        await self.redis.delete(self.user_key(user_id))

    async def invalidate_list(self):
        keys = await self.redis.keys('users:*')
        if keys:
            await self.redis.delete(*keys)

    async def invalidate_all(self):
        await self.invalidate_list()
        user_keys = await self.redis.keys('user:*')
        if user_keys:
            await self.redis.delete(*user_keys)


def get_user_cache(redis_client: redis.Redis) -> UserCache:
    return UserCache(redis_client=redis_client)
