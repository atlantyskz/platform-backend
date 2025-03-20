from contextlib import asynccontextmanager

import redis.asyncio as redis

redis_client = redis.Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True
)


async def get_redis_client():
     return redis_client
