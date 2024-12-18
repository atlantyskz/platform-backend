# import asyncio
# from typing import List, Optional
# import uuid
# from fastapi import APIRouter, Depends, Form, UploadFile,File,WebSocket
# from src.schemas.file_analysis import FileProcessingResponse
# from src.services.extractor import get_text_extractor,ITextExtractor
# from src.services.ai_analyzer import FileHandlerService, get_file_handler_service
# from src.core.worker import CustomRedisSettings
# import time
# from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
# from arq import create_pool
# from typing import List
# from datetime import datetime
# from pydantic import BaseModel

# handle_files_router = APIRouter(prefix='/api',tags=['CV/Vacancy Files Handler'])

# @handle_files_router.post('/handle_files', )
# async def handle_files(
# context_id: Optional[str] = Form(None),
# vacancy_requirement: UploadFile = File(...),
# cv_files: List[UploadFile] = File(...),
# text_extractor:ITextExtractor  = Depends(get_text_extractor),
# ):
#     try:
#         if not context_id:
#             context_id = str(uuid.uuid4())
#         vacancy_text = await text_extractor.extract_text(vacancy_requirement)
#         redis_pool = await create_pool(CustomRedisSettings())
#         task_ids = []
#         context_data = await redis_pool.hgetall(f"context:{context_id}")
#         existing_task_ids = context_data.get(b"task_ids", b"").decode("utf-8").split(",") if context_data else []
#         for cv_file in cv_files:
#             cv_text = await text_extractor.extract_text(cv_file)
#             job = await redis_pool.enqueue_job(
#             'analyze_cv_task',
#             vacancy_text,
#             cv_text
#             )
#             task_ids.append(job.job_id)
#             all_task_ids = existing_task_ids + task_ids
#         await redis_pool.hset(
#             f"context:{context_id}",
#             mapping={
#                 "task_ids": ",".join(all_task_ids),
#                 "status": "processing",
#                 "created_at": str(time.time())
#             }
#         )
#         return FileProcessingResponse(
#             context_id=context_id,
#             task_ids=all_task_ids,
#             status="processing",
#             created_at=time.time()
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))




# @handle_files_router.get('/analysis-results/context/{context_id}')
# async def get_context_analysis_results(context_id: str):
#     try:
#         redis_pool = await create_pool(CustomRedisSettings())
#         context_data = await redis_pool.hgetall(f"context:{context_id}")
        
#         print(f"context_data: {context_data}")

#         if not context_data:
#             raise HTTPException(status_code=404, detail="Context not found")

#         task_ids = context_data.get(b"task_ids", b"").decode("utf-8").split(",")
#         results=[]
#         for task_id in task_ids:
#             result = await redis_pool._get_job_result(f"hr_analyze:{task_id}".encode())
#             results.append(
#                 {
#                     "task_id":task_id,
#                     "status": "completed" if result else "processing",
#                     "result": result.result
#                 }
#             )

#         return {
#             "context_id": context_id,
#             "status": "processing" if any(r['status'] == "processing" for r in results) else "completed",
#             "tasks": results
#         }

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error fetching context results: {str(e)}"
#         )


# @handle_files_router.get('/analysis-results/contexts')
# async def get_all_contexts():
#     try:
#         redis_pool = await create_pool(CustomRedisSettings())
#         context_keys = await redis_pool.keys("context:*")
#         contexts = []
#         for key in context_keys:
#             context_id = key.decode("utf-8").split(":")[1]
#             context_data = await redis_pool.hgetall(key)
            
#             # Преобразуем task_ids в строку
#             task_ids = context_data.get(b"task_ids", b"").decode("utf-8").split(",")
#             contexts.append({
#                 "context_id": context_id,
#                 "task_ids": task_ids,
#                 "status": context_data.get(b"status", b"").decode("utf-8"),
#                 "created_at": context_data.get(b"created_at", b"").decode("utf-8")
#             })

#         return {"contexts": contexts}
    
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error fetching all contexts: {str(e)}"
#         )
