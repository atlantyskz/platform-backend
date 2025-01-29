import asyncio
import csv
import hashlib
import json
from io import BytesIO, StringIO
import math
import pprint
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import pprint
import json

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from io import BytesIO
from fastapi.responses import StreamingResponse
import json
from typing import List, Optional
import uuid
from fastapi import  HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from src.services.email import EmailService
from src.services.websocket import manager
from src.models.favorite_resume import FavoriteResume
from src.core.dramatiq_worker import process_resume
from src.core.exceptions import BadRequestException,NotFoundException
from src.repositories.assistant_session import AssistantSessionRepository
from src.repositories.assistant import AssistantRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.favorite_resume import FavoriteResumeRepository
from src.repositories.vacancy import VacancyRepository
from src.repositories.user import UserRepository
from src.repositories.chat_message_history import ChatHistoryMessageRepository
from src.core.exceptions import BadRequestException
from src.repositories.user import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.backend import BackgroundTasksBackend
from src.services.extractor import AsyncTextExtractor
from src.services.request_sender import RequestSender
from src.repositories.vacancy_requirement import VacancyRequirementRepository
from src.services.minio import MinioUploader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class HRAgentController:

    def __init__(self,session:AsyncSession,text_extractor:AsyncTextExtractor):
        self.session = session
        self.text_extractor = text_extractor
        self.request_sender = RequestSender()
        self.user_repo = UserRepository(session)
        self.favorite_repo = FavoriteResumeRepository(session)
        self.vacancy_repo = VacancyRepository(session)
        self.assistant_session_repo = AssistantSessionRepository(session)
        self.assistant_repo = AssistantRepository(session)
        self.bg_backend = BackgroundTasksBackend(session)
        self.history_repo = ChatHistoryMessageRepository(session)
        self.organization_repo = OrganizationRepository(session)
        self.requirement_repo = VacancyRequirementRepository(session)
        self.email_service = EmailService()
        self.minio_service = MinioUploader(
        host="minio:9000",  
        access_key="admin",
        secret_key="admin123",
        bucket_name="analyze-resumes"
    )
        self.manager = manager
        self.upload_progress = {}
        pdfmetrics.registerFont(TTFont('DejaVu', 'dejavu-sans-ttf-2.37/ttf/DejaVuSans.ttf'))


    async def create_vacancy(self,user_id:int, file: Optional[UploadFile], vacancy_text: Optional[str]):
        async with self.session.begin() as session:
            try:
                user_organization = await self.organization_repo.get_user_organization(user_id)
                if user_organization is None:
                    raise BadRequestException('You dont have organization')
                user_organization_info  = {
                    'company_name':user_organization.name,
                    'company_registered_address':user_organization.registered_address,
                    'company_phone':user_organization.phone_number,
                    'company_email':user_organization.email
                }
                if file and file.filename == "":
                    file = None

                if file and vacancy_text:
                    raise BadRequestException("Only one of 'file' or 'vacancy_text' should be provided")
                
                if not file and not vacancy_text:
                    raise BadRequestException("Either 'file' or 'vacancy_text' must be provided")        
                user_message = None
                if file:
                    content = await self.text_extractor.extract_text(file)
                    user_message = content
                elif vacancy_text:
                    user_message = vacancy_text
                messages = []  
                # Добавляем новое пользовательское сообщение в историю контекста
                messages.append({
                    "role": "user",
                    "content": f"{user_message} user info:{user_organization_info}"
                })


                llm_response = await self.request_sender._send_request(
                    llm_url=f'http://llm_service:8001/hr/generate_vacancy',
                    data={"messages": messages}
                )
                

                llm_title = llm_response.get('llm_response').get("job_title")
                assistant = await self.assistant_repo.get_assistant_by_name('ИИ Рекрутер')
                assist_session = await self.assistant_session_repo.create_session({
                    'user_id': user_id,
                    'title': llm_title,
                    'organization_id': user_organization.id,
                    'assistant_id': assistant.id
                }) 
                session_id = str(assist_session.id)
                
                await self.history_repo.create({
                    'session_id':session_id,
                    'user_id':user_id,
                    'role':'user',
                    'message':user_message
                })
                await self.history_repo.create({
                    'session_id':session_id,    
                    'user_id':user_id,
                    'role':'assistant',
                    'message':llm_response
                })
 
                vacancy = await self.vacancy_repo.add({
                    'title':llm_title,
                    'session_id':session_id,
                    'user_id':user_id,
                    'vacancy_text':llm_response
                })

                return {
                    'session_id':vacancy.session_id,
                    'title':vacancy.title,
                    'vacancy_text':vacancy.vacancy_text.get('llm_response')

                }
            except Exception as e:
                await session.rollback()
                raise e
            
    

    async def delete_vacancy_by_session_id(self,session_id:str,user_id:int):
        try:
            
            vacancy = await self.vacancy_repo.get_by_session_id(session_id)
            if vacancy is None:
                raise NotFoundException("Vacancy not found")
            if user_id != vacancy.user_id:
                raise BadRequestException('You dont have permission')
            await self.vacancy_repo.delete_vacancy(session_id)
            return {
                'success':True
            }
        except Exception as e:
            raise
    

    async def add_session_to_archive(self,user_id:int,session_id:UUID):
        try:
            session = await self.vacancy_repo.get_by_session_id(session_id)
            if session is None:
                raise NotFoundException("Session not found")
            if user_id != session.user_id:
                raise BadRequestException('You dont have permission')
            await self.assistant_session_repo.update_session(session_id,{'is_archived':True})
            await self.session.commit()
            return {
                'success':True
            }
        except Exception as e:
            raise


    async def get_generated_vacancy(self,session_id:str,):
        try:
            vacancy = await self.vacancy_repo.get_by_session_id(session_id)
            if vacancy is None:
                raise NotFoundException("Vacancy not found")
            return vacancy
        except Exception as e:
            raise


    async def update_vacancy(self,user_id,session_id:str, attributes:dict):
        async with self.session.begin():
            try:
                existing_vacancy = await self.get_generated_vacancy(session_id)
                if existing_vacancy.user_id != user_id:
                    raise BadRequestException("You dont have permissions to update vacancy")
                
                updated_vacancy = await self.vacancy_repo.get_by_session_id(session_id)
            
                updated_data = {
                    "vacancy_text": {
                        **updated_vacancy.vacancy_text,  
                        "llm_response": attributes.get('vacancy_text')    
                    }
                }
                
                updated_vacancy = await self.vacancy_repo.update_by_session_id(session_id, updated_data)
                await self.history_repo.create({
                    'session_id': session_id,
                    'user_id': existing_vacancy.user_id,
                    'role': 'user',
                    'message': updated_vacancy.vacancy_text
                })

                return {
                    "id": updated_vacancy.id,
                    "title": updated_vacancy.title,
                    "is_archived": updated_vacancy.is_archived,
                    "session_id": updated_vacancy.session_id,
                    "vacancy_text": updated_vacancy.vacancy_text
                }
            except Exception as e:
                raise e

    async def get_user_vacancies(self,user_id:int,is_archived: bool = False):
        try:
            user_vacancies = await self.vacancy_repo.get_by_user_id(user_id,is_archived)
            if user_vacancies is None:
                raise BadRequestException("Vacancies not found")
            return user_vacancies
        except Exception:
            raise

    async def get_user_sessions(self,user_id:int):
        try:
            user_sessions = await self.assistant_session_repo.get_by_user_id(user_id)
            return user_sessions
        except Exception:
            raise

    def get_text_hash(self,text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    async def session_creator(self, user_id: int, title: str):
        async with self.session.begin() as session:
            try:
                user_organization = await self.organization_repo.get_user_organization(user_id)
                if user_organization is None:
                    raise BadRequestException("You dont have organization")
                assistant = await self.assistant_repo.get_assistant_by_name("ИИ Рекрутер")
                assist_session = await self.assistant_session_repo.create_session({
                    'user_id': user_id,
                    'title': title,
                    'organization_id': user_organization.id,
                    'assistant_id': assistant.id
                })
                await self.vacancy_repo.add({
                    'title':title,
                    'session_id':assist_session.id,
                    'user_id':user_id
                })
                return {
                    'session_id': str(assist_session.id),
                    "title":assist_session.title,
                }
            except Exception as e:
                raise e

    async def delete_session(self,session_id:str):
        await self.assistant_session_repo.delete_session(session_id)
        return {
            "success":True
        }
    
    async def preview_cv(self,task_id):
        cv_task = await self.bg_backend.get_by_task_id(task_id)
        print(cv_task)
        if cv_task and cv_task.file_key is None:
            raise NotFoundException('File not found')
        file_stream = self.minio_service.get_file(cv_task.file_key)
        if not file_stream:
            raise HTTPException(status_code=404, detail="Файл не найден")
        
        return  StreamingResponse(
            file_stream,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={cv_task.task_id}.pdf"
            }
        )




    async def cv_analyzer(
        self, 
        user_id: int, 
        session_id: Optional[str], 
        vacancy_file: Optional[UploadFile], 
        vacancy_text: Optional[str],  
        resumes: List[UploadFile], 
    ):        
        user_organization = await self.organization_repo.get_user_organization(user_id)
        if user_organization is None:
            raise BadRequestException("You don't have an organization")
        
        if not vacancy_file and not vacancy_text:
            raise BadRequestException("You must upload a file or provide text")
        if len(resumes) == 0:
            raise BadRequestException("You must upload resume files")
        if len(resumes) > 100:
            raise BadRequestException("Too many resume files. Max number of resume files is 100")
        
        # Извлечение текста из вакансии
        if vacancy_file:
            vacancy_text = await self.text_extractor.extract_text(vacancy_file)
        elif vacancy_text:
            vacancy_text = vacancy_text.strip()
        vacancy_hash = self.get_text_hash(vacancy_text)

        # Работа с текстом вакансии
        existing_vacancy = await self.requirement_repo.get_text_by_hash(vacancy_hash)
        if existing_vacancy:
            vacancy_text = existing_vacancy.requirement_text
        else:
            await self.requirement_repo.create({
                "session_id": session_id,
                "requirement_hash": vacancy_hash,
                "requirement_text": vacancy_text
            })

        # Извлечение текста из резюме
        resume_texts = await asyncio.gather(*[self.text_extractor.extract_text(resume) for resume in resumes])
        for resume in resumes:
            resume.file.seek(0) 

        # Уникализация текстов
        unique_hashes = set()
        unique_batch = []

        for resume, text in zip(resumes, resume_texts):
            cleaned_text = text.strip()
            text_hash = self.get_text_hash(cleaned_text)

            if text_hash not in unique_hashes:
                unique_hashes.add(text_hash)
                unique_batch.append((resume, cleaned_text))

        if not unique_batch:
            raise BadRequestException("No unique resumes found")

        unique_resumes = [resume for resume, _ in unique_batch]
        minio_uploader =self.minio_service

        try:
            file_info = await minio_uploader.save_files_in_minio(unique_resumes, session_id)
        except BadRequestException as e:
            raise e

        # Сохранение уникальных текстов и файлов
        total_files = len(unique_batch)
        processed_count = 0
        all_task_ids = []

        for (resume, resume_text), (file_url, file_key) in zip(unique_batch, file_info):
            task_id = str(uuid.uuid4())
            await self.bg_backend.create_task({
                "task_id": task_id,
                "session_id": session_id,
                "task_type": "hr cv analyze",
                "task_status": "pending",
                "file_key": str(file_key),
            })

            process_resume.send(task_id, vacancy_text, resume_text)
            processed_count += 1
            await self.send_progress(user_id, processed_count=processed_count, total_files=total_files)
            all_task_ids.append(task_id)

        return {"session_id": session_id, "tasks": all_task_ids, "tasks_count": len(all_task_ids)}




    async def send_progress(self, user_id: int, processed_count: int, total_files: int):
        """Отправляет прогресс пользователю через WebSocket"""
        progress_data = {
            "user_id": str(user_id),
            "processed_count": processed_count,
            "total_files": total_files,
            "progress_percent": round((processed_count / total_files) * 100, 2),
        }
        await self.manager.send_json(user_id, progress_data)

    async def ws_progress(self, websocket: WebSocket, user_id: int):
        await self.manager.connect(user_id, websocket)

        print("12312321")
        await self.manager.send_json(1,{"hi":"user"})
        try:
            while True:
                await self.manager.send_json(123123,{"hi":"user"})
                await websocket.receive_text()
        except Exception as e:
            print(f"WebSocket connection error: {e}")
        finally:
            await self.manager.disconnect(user_id)


        

    async def delete_resume_by_session_id(self,user_id:int, session_id:str):
        try:
            
            assistant_session = await self.assistant_session_repo.get_by_session_id(session_id)
            if assistant_session is None:
                raise NotFoundException("Assistant session not found")
            if user_id != assistant_session.user_id:
                raise BadRequestException('You dont have permission')
            await self.assistant_session_repo.delete_session(session_id)
            return {
                'success':True
            }
        except Exception as e:
            raise e

    async def export_to_csv(self, session_id: str):
        results = await self.bg_backend.get_session_results_to_export(session_id)
        
        csv_output = StringIO()
        fieldnames = [
            "fullname", 
            "gender", 
            "age", 
            "birth_date", 
            "phone_number", 
            "email", 
            "preferred_contact", 
            "location", 
            "languages", 
            "desired_position", 
            "specializations", 
            "employment_type", 
            "work_schedule", 
            "desired_salary", 
            "overall_years_experience", 
            "experience_details", 
            "education", 
            "skills", 
            "matching_percentage", 
            "overall_comment"
        ]
        
        writer = csv.DictWriter(csv_output, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for result in results:
            try:
                if isinstance(result.result_data, str):
                    result_data = json.loads(result.result_data)
                else:
                    result_data = result.result_data 

                candidate_info   = result_data.get("candidate_info", {})
                job_preferences  = result_data.get("job_preferences", {})
                analysis         = result_data.get("analysis", {})
                experience_obj   = result_data.get("experience", {})
                experience_list  = experience_obj.get("details", [])
                overall_years    = experience_obj.get("overall_years", "")

                experience_details = []
                for exp in experience_list:
                    duration = exp.get("duration", "N/A")
                    company = exp.get("company_name", "N/A")
                    role = exp.get("role", "")
                    experience_details.append(f"{duration}, {company}, {role}")
                experience_str = " | ".join(experience_details)

                education_obj   = result_data.get("education", {})
                education_list  = education_obj.get("degrees", [])
                education_str   = ", ".join(education_list)

                skills_list     = result_data.get("skills", [])
                skills_str      = ", ".join(skills_list)

                languages_list  = candidate_info.get("languages", [])
                languages_str   = ", ".join(languages_list)

                row = {
                    "fullname": candidate_info.get("fullname", ""),
                    "gender": candidate_info.get("gender", ""),
                    "age": candidate_info.get("age", ""),
                    "birth_date": candidate_info.get("birth_date", ""),
                    "phone_number": candidate_info.get("contacts", {}).get("phone_number", ""),
                    "email": candidate_info.get("contacts", {}).get("email", ""),
                    "preferred_contact": candidate_info.get("contacts", {}).get("preferred_contact", ""),
                    "location": candidate_info.get("location", ""),
                    "languages": languages_str,
                    "desired_position": job_preferences.get("desired_position", ""),
                    "specializations": ", ".join(job_preferences.get("specializations", [])),
                    "employment_type": job_preferences.get("employment_type", ""),
                    "work_schedule": job_preferences.get("work_schedule", ""),
                    "desired_salary": job_preferences.get("desired_salary", ""),
                    "overall_years_experience": overall_years,
                    "experience_details": experience_str,
                    "education": education_str,
                    "skills": skills_str,
                    "matching_percentage": analysis.get("matching_percentage", ""),
                    "overall_comment": analysis.get("overall_comment", "")
                }

                writer.writerow(row)
            except Exception as e:
                print(f"Error processing result with id={result.id}: {e}")
        
        csv_output.seek(0)
        csv_data = csv_output.getvalue()

        response = StreamingResponse(
            iter([csv_data]),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = "attachment; filename=export.csv"
        return response
    

    async def get_cv_analyzer_result_by_session_id(self, session_id: str, user_id: int, offset: Optional[int], limit: Optional[int]):
        results = await self.bg_backend.get_results_by_session_id(session_id, user_id, offset, limit)
        return {
            "session_id": session_id,
            "results": [
                {
                    "id": res[0].id, 
                    "task_id":res[0].task_id,
                    "result_data": res[0].result_data,
                    "is_favorite": res[1] 
                }
                for res in results
            ]
        }
    async def add_resume_to_favorites(self,user_id: int, resume_id: int):
        try:
            exist_resume = await self.favorite_repo.get_favorite_resumes_by_resume_id(resume_id)
            if exist_resume:
                raise BadRequestException('Already exist')
            if await self.favorite_repo.get_resume(resume_id) is None:
                raise BadRequestException('Not Found')
            favorite_resume = await self.favorite_repo.add({
                "user_id":user_id,
                "resume_id":resume_id
            })
            await self.session.commit()
            await self.session.refresh(favorite_resume)
            return favorite_resume
        except Exception:
            raise
    
    
    async def delete_from_favorites(self, user_id: int,resume_id: int):
        try:
            resume = await self.favorite_repo.delete_by_resume_id(user_id=user_id,resume_id=resume_id)
            if resume is None:
                raise BadRequestException('Invalid request or resume id')
            await self.session.delete(resume)
            await self.session.commit()
            return {
                'success':True
            }
        except Exception:
            raise


    async def get_favorite_resumes(self,user_id: int,session_id:str):
        favorite_resumes = await self.favorite_repo.get_favorite_resumes_by_user_id(user_id, session_id)
        return favorite_resumes




    async def ws_update_vacancy_by_ai(self, session_id: int, websocket: WebSocket):
        try:
            await websocket.accept()

            while True:
                user_message = await websocket.receive_json()
                user_content = user_message.get('message')
                vacancy = await self.vacancy_repo.get_by_session_id(session_id)
                if vacancy is None:
                    await websocket.send_json({'error': 'Vacancy not found or Organization not found'})
                    await websocket.close()
                    return
                await websocket.send_json({'vacancy_text': vacancy.vacancy_text})

                await self.history_repo.create({
                    'session_id': session_id,
                    'user_id': vacancy.user_id,
                    'role': 'user',
                    'message': user_content
                })

                history_records = await self.history_repo.get_all_by_session_id(session_id)
                messages = []
                for record in history_records:
                    content = record.message
                    if not isinstance(content, str):
                        content = json.dumps(content, ensure_ascii=False)
                    messages.append({
                        "role": record.role,
                        "content": content
                    })

                messages.append({
                    "role": "user",
                    "content": user_content
                })

                try:
                    llm_response = await self.request_sender._send_request(
                        data={'messages': messages},
                        llm_url='http://llm_service:8001/hr/generate_vacancy'
                    )
                    await self.vacancy_repo.update_by_session_id(session_id, {
                        "vacancy_text": llm_response
                    })

                    assistant_content = llm_response.get('llm_response')
                    # Преобразуем assistant_content в строку, если он не строка
                    if not isinstance(assistant_content, str):
                        assistant_content = json.dumps(assistant_content, ensure_ascii=False)

                    await self.history_repo.create({
                        'session_id': session_id,
                        'user_id': vacancy.user_id,
                        'role': 'assistant',
                        'message': assistant_content
                    })

                    await self.session.commit()
                    updated_vacancy = await self.vacancy_repo.get_by_session_id(session_id)
                    await websocket.send_json({'vacancy_text': updated_vacancy.vacancy_text})

                except Exception as e:
                    await websocket.send_json({'error': f'Failed to generate updated vacancy: {str(e)}'})
                    break
        except Exception as e:
            await websocket.send_json({'error': f'An unexpected error occurred - {str(e)}'})
            await websocket.close()

    async def ws_review_results_by_ai(self,session_id:str, websocket: WebSocket,user_id:int):
        try:
            session_results = await self.bg_backend.get_results_by_session_id_ws(session_id)
            await websocket.accept()
            
            await websocket.send_json({
                "session_id": session_id,
                "results": [
                {
                    "id": res.id, 
                    "result_data": res.result_data
                }
                for res in session_results
                ]
            })

            await websocket.send_json(user_id)
            while True:
                try:
                    user_message = await websocket.receive_json()
                    data = {
                        "user_message": user_message.get("message"),
                        "resumes": {
                            "session_id": session_id,
                            "results": [
                                {"id": session_result.id, "result_data": session_result.result_data}
                                for session_result in session_results
                            ]
                        }
                    }
                    llm_response = await self.request_sender._send_request(
                        data=data,
                        llm_url="http://llm_service:8001/hr/review_cv_results"
                    )
                    # Отправляем результаты клиенту
                    await websocket.send_json({"review_results": llm_response})
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    try:
                        await websocket.send_json({"error": str(e)})
                    except RuntimeError:
                        break
        except Exception as e:
            await websocket.send_json({"error": str(e)})
        finally:
            pass

        
    async def generate_pdf(self, session_id: str):
        vacancy = await self.vacancy_repo.get_by_session_id(session_id)
        buffer = BytesIO()

        # Получаем данные как байты или словарь
        vacancy_text = vacancy.vacancy_text
        if not vacancy_text:
            raise HTTPException(status_code=400, detail="vacancy_text отсутствует или пустой.")

        # Определяем тип данных и получаем vacancy_data
        if isinstance(vacancy_text, bytes):
            try:
                vacancy_text_str = vacancy_text.decode('utf-8')
                vacancy_data = json.loads(vacancy_text_str)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Ошибка декодирования vacancy_text: {e}")
        elif isinstance(vacancy_text, str):
            try:
                vacancy_data = json.loads(vacancy_text)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Некорректный JSON: {e}")
        elif isinstance(vacancy_text, dict):
            vacancy_data = vacancy_text
        else:
            raise HTTPException(status_code=400, detail="Неподдерживаемый тип данных для vacancy_text.")

        llm_response = vacancy_data.get('llm_response', vacancy_data)
        job_title = llm_response.get('job_title', 'Не указано')
        specialization = llm_response.get('specialization', 'Не указано')
        salary_range = llm_response.get('salary_range', 'Не указано')
        company_name = llm_response.get('company_name', 'Не указано')
        experience_required = llm_response.get('experience_required', 'Не указано')
        work_format = llm_response.get('work_format', 'Не указано')
        work_schedule = llm_response.get('work_schedule', 'Не указано')
        responsibilities = llm_response.get('responsibilities', [])
        requirements = llm_response.get('requirements', [])
        conditions = llm_response.get('conditions', [])
        skills = llm_response.get('skills', [])
        address = llm_response.get('address', 'Не указано')
        contacts = llm_response.get('contacts', {})
        location = llm_response.get('location', 'Не указано')

        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter  # получаем размеры страницы
        margin = 72  # отступ в 1 дюйм
        line_height = 15  # высота строки

        # Настраиваем шрифт
        c.setFont("DejaVu", 12)

        def wrap_text_in_width(text, available_width):
            """Разбивает текст на строки, помещающиеся в заданную ширину."""
            return simpleSplit(text, "DejaVu", 12, available_width)

        def add_wrapped_text(x, y, text, available_width):
            """Добавляет текст с переносом строк и возвращает новую позицию y."""
            nonlocal y_position
            
            # Если текст короче доступной ширины, добавляем его как есть
            if c.stringWidth(text, "DejaVu", 12) <= available_width:
                if y_position < margin:
                    c.showPage()
                    c.setFont("DejaVu", 12)
                    y_position = height - margin
                c.drawString(x, y_position, text)
                y_position -= line_height
                return y_position

            # Разбиваем длинный текст на строки
            lines = wrap_text_in_width(text, available_width)
            for line in lines:
                if y_position < margin:
                    c.showPage()
                    c.setFont("DejaVu", 12)
                    y_position = height - margin
                c.drawString(x, y_position, line)
                y_position -= line_height
            return y_position

        def add_section(title, items, indent=0):
            """Добавляет раздел с заголовком и списком элементов."""
            nonlocal y_position
            
            # Добавляем заголовок
            available_width = width - (2 * margin) - indent
            y_position = add_wrapped_text(margin + indent, y_position, title, available_width)
            y_position -= 5  # дополнительный отступ после заголовка
            
            # Добавляем элементы списка
            for item in items:
                bullet_text = f"• {item}"
                y_position = add_wrapped_text(margin + indent + 15, y_position, bullet_text, available_width - 15)
            
            y_position -= 10  # отступ после секции

        # Начальная позиция
        y_position = height - margin

        # Добавляем основную информацию
        main_info = [
            f"Job Title: {job_title}",
            f"Specialization: {specialization}",
            f"Salary Range: {salary_range}",
            f"Company Name: {company_name}",
            f"Experience Required: {experience_required}",
            f"Work Format: {work_format}",
            f"Work Schedule: {work_schedule}",
            f"Location: {location}"
        ]

        for info in main_info:
            y_position = add_wrapped_text(margin, y_position, info, width - (2 * margin))

        # Добавляем разделы
        y_position -= 20
        sections = [
            ("Responsibilities:", responsibilities),
            ("Requirements:", requirements),
            ("Conditions:", conditions),
            ("Skills:", skills)
        ]

        for title, items in sections:
            if items:  # проверяем, что список не пустой
                add_section(title, items)

        # Добавляем контактную информацию
        y_position -= 10
        contact_title = "Contact Information:"
        y_position = add_wrapped_text(margin, y_position, contact_title, width - (2 * margin))
        
        if contacts:
            phone = contacts.get('phone', 'Не указано')
            email = contacts.get('email', 'Не указано')
            contact_info = [
                f"Phone: {phone}",
                f"Email: {email}"
            ]
            for info in contact_info:
                y_position = add_wrapped_text(margin + 20, y_position, info, width - (2 * margin) - 20)

        # Сохраняем PDF
        c.save()
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=vacancy.pdf"}
        )
        

    def update_upload_progress(self, user_id: int, uploaded: int, total: int):
        self.upload_progress[user_id] = {"uploaded": uploaded, "total": total}

    def get_upload_progress(self, user_id: int):
        return self.upload_progress.get(user_id, {"uploaded": 0, "total": 0})
    

    async def rename_session(self,user_id,session_id,new_title: str):
        async with self.session.begin() as session:
            user_session =  await self.assistant_session_repo.get_by_user_id(user_id)
            print(user_session)
            if user_session is None:
                raise BadRequestException('Session not found')
            await self.assistant_session_repo.update_session(session_id,{
                'title':new_title
            })
            return {
                'success':True
            }
        
    async def remove_session_from_archive(self,user_id,session_id):
        try:
            session = await self.vacancy_repo.get_by_session_id(session_id)
            if session is None:
                raise NotFoundException("Session not found")
            if user_id != session.user_id:
                raise BadRequestException('You dont have permission')
            await self.assistant_session_repo.update_session(session_id,{'is_archived':False})
            await self.session.commit()
            return {
                'success':True
            }
        except Exception as e:
            raise