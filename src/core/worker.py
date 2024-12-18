# import aioredis
# from arq import create_pool
# from arq.connections import RedisSettings
# from typing import List

# from fastapi import Depends

# from src.services.request_sender import RequestSender

# class CustomRedisSettings(RedisSettings):
#     result_key_prefix = 'hr_analyze:'

# async def startup(ctx):
#     ctx['redis'] = await create_pool(CustomRedisSettings(port=6378))

# async def analyze_cv_task(ctx, data:dict) -> dict:
#     """Task for analyzing one CV"""
#     try:
#         request_sender = RequestSender()
#         result = await request_sender._send_request(data=data)
#         print(result)
#         return result
#     except Exception as e:
#         return {"status": "error", "error": str(e)}
    
# async def shutdown(ctx):
#     await ctx['redis'].close()

# class WorkerSettings:
#     functions = [analyze_cv_task]
#     redis_settings = CustomRedisSettings()
#     on_startup = startup
#     on_shutdown = shutdown


# async def get_redis_pool():
#     pool = await create_pool(CustomRedisSettings())
#     try:
#         yield pool
#     finally:
#         await pool.close()

