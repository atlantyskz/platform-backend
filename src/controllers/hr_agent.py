import csv
import json
from io import StringIO
from uuid import uuid4
from typing import List, Optional
from fastapi import  UploadFile, WebSocket
from fastapi.responses import StreamingResponse
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

    async def create_vacancy(self,user_id:int,title:str, file: Optional[UploadFile], vacancy_text: Optional[str]):
        if file and file.filename == "":
            file = None

        if file and vacancy_text:
            raise BadRequestException("Only one of 'file' or 'vacancy_text' should be provided")
        
        if not file and not vacancy_text:
            raise BadRequestException("Either 'file' or 'vacancy_text' must be provided")
        
        user_message = None
        if file:
            content = await file.read()
            try:
                user_message = content.decode('utf-8')
            except UnicodeDecodeError:
                user_message = content.decode('latin1') 
        elif vacancy_text:
            user_message = vacancy_text

        llm_response = await self.request_sender._send_request(
            llm_url=f'http://llm_service:8001/hr/generate_vacancy',
            data={"user_message": user_message}
        )
        vacancy = await self.vacancy_repo.add({
            'title':title,
            'user_id':user_id,
            'vacancy_text':llm_response
        })

        return vacancy
    
    async def get_generated_vacancy(self,vacancy_id:int,):
        try:
            vacancy = await self.vacancy_repo.get_by_id(vacancy_id)
            if vacancy is None:
                raise NotFoundException("Vacancy not found")
            return vacancy
        except Exception as e:
            raise


    async def update_vacancy(self,user_id,vacancy_id:int, attributes:dict):
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

    async def get_user_vacancies(self,user_id:int):
        try:
            user_vacancies = await self.vacancy_repo.get_by_user_id(user_id)
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
    

    async def get_cv_analyzer_result_by_session_id(self, session_id: str,offset:Optional[int], limit:Optional[int]):
        results = await self.bg_backend.get_results_by_session_id(session_id,offset,limit)
        return {
            "session_id": session_id,
            "results": [
                {"id": res.id, "result_data": res.result_data} for res in results
            ]
        }

    async def add_resume_to_favorites(self,user_id:int, resume_id:int):
        favorite_resume = await self.favorite_repo.add({
            "user_id":user_id,
            "resume_id":resume_id
        })
        await self.session.commit()
        await self.session.refresh(favorite_resume)
        return favorite_resume
    
    async def get_favorite_resumes(self,user_id: int,session_id:str):
        favorite_resumes = await self.favorite_repo.get_favorite_resumes_by_user_id(user_id, session_id)
        return favorite_resumes

    async def ws_update_vacancy_by_ai(self,vacancy_id:int, websocket: WebSocket):
        try:
            vacancy = await self.vacancy_repo.get_by_id(vacancy_id)
            await websocket.accept()
            if vacancy is None:
                await websocket.send_json({'error':'Vacancy not found'})
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
        

