from abc import ABC,abstractmethod
import time
from typing import Optional

from fastapi import Depends
from src.schemas.file_analysis import ProcessingContext
from src.core.worker import get_redis_pool


class RedisTaskQueue:
    def __init__(self, redis_pool):
        self.redis_pool = redis_pool
    
    async def enqueue(self, task_name: str, *args) -> Optional[str]:
        try:
            job = await self.redis_pool.enqueue_job(task_name, *args)
            return job.job_id
        except Exception as e:
            print(f"Error enqueueing task: {str(e)}")
            return None

class RedisContextStorage:
    def __init__(self, redis_pool):
        self.redis_pool = redis_pool
    
    async def _save_context(self, context):
        try:
            await self.redis_pool.hset(
                f"context:{context.context_id}",
                mapping={
                    "task_ids": ",".join(context.task_ids),
                    "status": context.status,
                    "created_at": str(context.created_at)
                }
            )
        except Exception as e:
            print(f"Error saving context: {str(e)}")
            return None

    async def _get_existing_context(self, context_id):
        try:
            data = await self.redis_pool.hgetall(f"context:{context_id}")
            if not data:
                return ProcessingContext.create_new(context_id)
            
            return ProcessingContext(
                context_id=context_id,
                task_ids=data.get(b"task_ids", b"").decode("utf-8").split(","),
                status=data.get(b"status", b"processing").decode("utf-8"),
                created_at=float(data.get(b"created_at", str(time.time())).decode("utf-8"))
            )
        except Exception as e:
            print(f"Error getting context: {str(e)}")
            return None
        
    async def get_task_results_by_context(self, context_id):
        try:
            # Получаем контекст по context_id
            context_data = await self.redis_pool.hgetall(f"context:{context_id}")
            if not context_data:
                return {"error": "Context not found"}
            
            # Извлекаем task_ids из контекста
            task_ids = context_data.get(b"task_ids", b"").decode("utf-8").split(",")
            
            # Получаем результаты для каждого task_id
            task_results = []
            for task_id in task_ids:
                task_result = await self.redis_pool.hgetall(f"task:{task_id}")
                print(task_result)
            return {
                "context_id": context_id,
                "task_results": task_results
            }

        except Exception as e:
            print(f"Error getting task results for context {context_id}: {str(e)}")
            return {"error": str(e)}

        
async def get_redis_context_storage(redis_pool = Depends(get_redis_pool)):
    return RedisContextStorage(redis_pool)

async def get_task_queue(redis_pool = Depends(get_redis_pool)):
    return RedisTaskQueue(redis_pool)

