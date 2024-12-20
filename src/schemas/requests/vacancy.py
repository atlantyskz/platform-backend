from pydantic import BaseModel,field_validator

class VacancyText(BaseModel):
    job_title: str
    specialization: str
    salary_range: str
    company_name: str
    experience_required: str
    work_format: str
    work_schedule: str
    responsibilities: list[str]
    requirements: list[str]
    conditions: list[str]
    skills: list[str]
    address: str
    contacts: str
    location: str

    @field_validator("job_title","company_name")
    def check_non_empty(cls,v):
        if not v:
            raise ValueError("Field cant not be empty")
        return v
    

class VacancyTextUpdate(BaseModel):
    vacancy_text: VacancyText