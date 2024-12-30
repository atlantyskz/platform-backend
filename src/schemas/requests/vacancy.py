from typing import List, Optional
from pydantic import BaseModel, Field,field_validator

class VacancyText(BaseModel):
    job_title: str
    specialization: Optional[str] = Field(None)
    salary_range: Optional[str] = Field(None)
    company_name: str
    experience_required: Optional[str] = Field(None)
    work_format: Optional[str] = Field(None)
    work_schedule: Optional[str] = Field(None)
    responsibilities: Optional[List[str]] = Field(None)
    requirements: Optional[List[str]] = Field(None)
    conditions: Optional[List[str]] = Field(None)
    skills: Optional[List[str]] = Field(None)
    address: Optional[str] = Field(None)
    contacts: Optional[dict] = Field(None)
    location: Optional[str] = Field(None)

    @field_validator("job_title","company_name")
    def check_non_empty(cls,v):
        if not v:
            raise ValueError("Field cant not be empty")
        return v
    

class VacancyTextUpdate(BaseModel):
    vacancy_text: VacancyText

class VacancyTextCreate(BaseModel):
    vacancy_text: str