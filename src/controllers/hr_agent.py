import csv
import json
from io import BytesIO, StringIO
from uuid import UUID, uuid4
from typing import List, Optional
from fastapi import  HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from src.models.favorite_resume import FavoriteResume
from src.core.dramatiq_worker import process_resume
from src.core.exceptions import BadRequestException,NotFoundException
from src.repositories.assistant_session import AssistantSessionRepository
from src.repositories.assistant import AssistantRepository
from src.repositories.organization import OrganizationRepository
from src.repositories.favorite_resume import FavoriteResumeRepository
from src.repositories.vacancy import VacancyRepository
from src.repositories.user import UserRepository
from src.core.exceptions import BadRequestException
from src.repositories.user import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.backend import BackgroundTasksBackend
from src.services.extractor import AsyncTextExtractor
from src.services.request_sender import RequestSender
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
        self.organization_repo = OrganizationRepository(session)
        pdfmetrics.registerFont(TTFont('DejaVu', 'dejavu-sans-ttf-2.37/ttf/DejaVuSans.ttf'))


    async def create_vacancy(self,user_id:int, file: Optional[UploadFile], vacancy_text: Optional[str]):
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
            print(content)
            user_message = content
        elif vacancy_text:
            user_message = vacancy_text
        llm_response = await self.request_sender._send_request(
            llm_url=f'http://llm_service:8001/hr/generate_vacancy',
            data={"user_message": user_message + f'user info:{user_organization_info}'}
        )
        vacancy = await self.vacancy_repo.add({
            'title':llm_response.get('llm_response').get("job_title"),
            'user_id':user_id,
            'vacancy_text':llm_response
        })

        return vacancy
    

    async def delete_vacancy_by_vacancy_id(self,vacancy_id:str,user_id:int):
        try:
            
            vacancy = await self.vacancy_repo.get_by_id(vacancy_id)
            if vacancy is None:
                raise NotFoundException("Vacancy not found")
            if user_id != vacancy.user_id:
                raise BadRequestException('You dont have permission')
            await self.vacancy_repo.delete_vacancy(vacancy_id)
            return {
                'success':True
            }
        except Exception as e:
            raise
    

    async def add_vacancy_to_archive(self,user_id:int,vacancy_id:UUID):
        try:
            vacancy = await self.vacancy_repo.get_by_id(vacancy_id)
            if vacancy is None:
                raise NotFoundException("Vacancy not found")
            if user_id != vacancy.user_id:
                raise BadRequestException('You dont have permission')
            await self.vacancy_repo.update_to_archive(vacancy_id,{'is_archived':True})
            await self.session.commit()
            return {
                'success':True
            }
        except Exception as e:
            raise


    async def get_generated_vacancy(self,vacancy_id:str,):
        try:
            vacancy = await self.vacancy_repo.get_by_id(vacancy_id)
            if vacancy is None:
                raise NotFoundException("Vacancy not found")
            return vacancy
        except Exception as e:
            raise


    async def update_vacancy(self,user_id,vacancy_id:str, attributes:dict):
        try:
            existing_vacancy = await self.get_generated_vacancy(vacancy_id)
            if existing_vacancy.user_id != user_id:
                raise BadRequestException("You dont have permissions to update vacancy")
            updated_vacancy = await self.vacancy_repo.update_by_id(vacancy_id,attributes.get("vacancy_text"))
            await self.session.commit()
            await self.session.refresh(updated_vacancy)
            return updated_vacancy
        except Exception:
            raise

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

    async def cv_analyzer(self, user_id: int, session_id: Optional[str], vacancy_file: UploadFile, resumes: List[UploadFile], title:Optional[str]):
        user_organization = await self.organization_repo.get_user_organization(user_id)
        if user_organization is None:
            raise BadRequestException("You dont have organization")
        if len(resumes) == 0 and len(vacancy_file) == 0:
            raise BadRequestException("You must upload files")
        if len(resumes) > 100:
            raise BadRequestException("Too many resume files. Max number of resume files 100")
        if (session_id is None) and (title is not None):
            session = await self.assistant_session_repo.create_session({
                'user_id': user_id,
                'title':title,
                'organization_id': user_organization.id,
                'assistant_id': 1
            })  
            session_id = str(session.id)
        vacancy_text = await self.text_extractor.extract_text(vacancy_file)
        task_ids = []

        for resume in resumes:
            resume_text =  await self.text_extractor.extract_text(resume)
            task_id = str(uuid4())
            await self.bg_backend.create_task({
                "task_id":task_id,
                "session_id":session_id,
                "task_type":"hr cv analyze",
                "task_status":"pending"
            })
            
            process_resume.send( task_id, vacancy_text, resume_text)
            
            task_ids.append(task_id)
        
        return {"session_id": session_id, "tasks": task_ids}

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
        results = await self.bg_backend.get_results_by_session_id(session_id)
        
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
                    "result_data": res[0].result_data,
                    "is_favorite": res[1] 
                }
                for res in results
            ]
        }
    async def add_resume_to_favorites(self,user_id: int, resume_id: int):
        favorite_resume = await self.favorite_repo.add({
            "user_id":user_id,
            "resume_id":resume_id
        })
        await self.session.commit()
        await self.session.refresh(favorite_resume)
        return favorite_resume
    
    
    async def delete_from_favorites(self, user_id: int,resume_id: int):
        deleted = await self.favorite_repo.delete_by_resume_id(user_id,resume_id)
        if deleted:
            return {
                'success':True
            }
        else:
            raise BadRequestException("Bad request")


    async def get_favorite_resumes(self,user_id: int,session_id:str):
        favorite_resumes = await self.favorite_repo.get_favorite_resumes_by_user_id(user_id, session_id)
        return favorite_resumes


    async def ws_update_vacancy_by_ai(self,vacancy_id:int ,websocket: WebSocket):
        try:
            vacancy = await self.vacancy_repo.get_by_id(vacancy_id)
            await websocket.accept()
            if vacancy is None :
                await websocket.send_json({'error':'Vacancy not found or Organization not found'})
                await websocket.close()
                return

            await websocket.send_json(vacancy.vacancy_text)
            while True:
                user_message = await websocket.receive_json()
                data = {
                    'user_message':user_message.get('message'),
                    'vacancy_to_update':vacancy.vacancy_text
                }
                try:
                    llm_response = await self.request_sender._send_request(data=data,llm_url='http://llm_service:8001/hr/generate_vacancy')
                    await websocket.send_json({
                        'updated_vacancy':llm_response
                    })
                except Exception:
                    await websocket.send_json({'error':'Failed to generate updated vacancy'})
                    break
        except Exception:
            await websocket.send_json({'error': 'An unexpected error occurred'})
            await websocket.close()
        

    async def ws_review_results_by_ai(self,session_id:str, websocket: WebSocket,user_id:int):
        try:
            session_results = await self.bg_backend.get_results_by_session_id(session_id,user_id)

            await websocket.accept()
            

            await websocket.send_json({
                "session_id": session_id,
                "results": [
                {
                    "id": res[0].id, 
                    "result_data": res[0].result_data,
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

                    # Запрос к LLM
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
            await websocket.close()        

    async def generate_pdf(self, vacancy_id: str):
        vacancy = await self.vacancy_repo.get_by_id(vacancy_id)
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

        llm_response = vacancy_data.get('llm_response', {})
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

        # Создаем PDF с помощью reportlab
        c = canvas.Canvas(buffer, pagesize=letter)

        # Настраиваем шрифт
        c.setFont("DejaVu", 12)

        # Функция для добавления текста и обновления позиции
        def add_text(x, y, text, offset=20):
            nonlocal y_position
            if y_position < 50:
                c.showPage()
                c.setFont("DejaVu", 12)
                y_position = 750
            c.drawString(x, y_position, text)
            y_position -= offset

        # Начальная позиция по Y
        y_position = 750

        # Добавляем основные поля
        add_text(100, y_position, f"Job Title: {job_title}")
        add_text(100, y_position, f"Specialization: {specialization}")
        add_text(100, y_position, f"Salary Range: {salary_range}")
        add_text(100, y_position, f"Company Name: {company_name}")
        add_text(100, y_position, f"Experience Required: {experience_required}")
        add_text(100, y_position, f"Work Format: {work_format}")
        add_text(100, y_position, f"Work Schedule: {work_schedule}")
        add_text(100, y_position, f"Location: {location}")

        # Добавляем разделы с заголовками и списками
        sections = [
            ("Responsibilities:", responsibilities),
            ("Requirements:", requirements),
            ("Conditions:", conditions),
            ("Skills:", skills)
        ]

        for title, items in sections:
            y_position -= 20
            add_text(100, y_position, title)
            for item in items:
                add_text(120, y_position, f"- {item}", offset=15)

        # Добавляем контактную информацию
        y_position -= 20
        add_text(100, y_position, "Contact Information:")
        if contacts:
            phone = contacts.get('phone', 'Не указано')
            email = contacts.get('email', 'Не указано')
            add_text(120, y_position, f"Phone: {phone}", offset=15)
            add_text(120, y_position, f"Email: {email}", offset=15)

        # Сохраняем PDF
        c.showPage()
        c.save()

        # Возвращаем PDF как StreamingResponse
        buffer.seek(0)  # Возвращаемся к началу буфера перед отправкой
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=vacancy.pdf"}
        )