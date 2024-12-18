# from typing import List, Optional
# from fastapi import Depends, UploadFile
# from src.schemas.file_analysis import FileProcessingResponse
# from src.services.extractor import ITextExtractor,AsyncTextExtractor, get_text_extractor
# from src.services.redis_service import *
# from src.services.request_sender import *

# class FileHandlerService:
#     def __init__(self, text_extractor: ITextExtractor, context_storage: RedisContextStorage, task_queue: RedisTaskQueue,):
#         self.text_extractor = text_extractor
#         self.context_storage = context_storage
#         self.task_queue = task_queue

#     async def handle_files(self, context_id: Optional[str], vacancy_file: UploadFile, cv_files: List[UploadFile]) -> FileProcessingResponse:
#         context = await self.context_storage._get_existing_context(context_id)
#         vacancy_text = await self.text_extractor.extract_text(vacancy_file)
#         task_ids = []
#         for cv_file in cv_files:
#             cv_text = await self.text_extractor.extract_text(cv_file)
#             data = {
#                 "vacancy_text":vacancy_text,
#                 "cv_text":cv_text
#             }
#             task_id = await self.task_queue.enqueue('analyze_cv_task',data)
#             task_ids.append(task_id)

#         context.task_ids.extend(task_ids)
#         context.status = "processing"
#         await self.context_storage._save_context(context)

#         return FileProcessingResponse(
#             context_id=context.context_id,
#             task_ids=context.task_ids,
#             status=context.status,
#             created_at=context.created_at
#         )
    



# async def get_file_handler_service(
#     text_extractor: ITextExtractor = Depends(get_text_extractor),
#     context_storage: RedisContextStorage = Depends(get_redis_context_storage),
#     task_queue: RedisTaskQueue = Depends(get_task_queue),
# ) -> FileHandlerService:
#     return FileHandlerService(
#         text_extractor=text_extractor,
#         context_storage=context_storage,
#         task_queue=task_queue,
#     )
