from pydantic import BaseModel, Field, constr

class UserFeedbackRequest(BaseModel):
    experience_rating: float = Field(..., ge=1, le=5, description="Рейтинг опыта: минимум 1, максимум 5")
    vacancy_creation_rating: float = Field(..., ge=1, le=5, description="Рейтинг создания вакансии: минимум 1, максимум 5")
    resume_analysis_rating: float = Field(..., ge=1, le=5, description="Рейтинг анализа резюме: минимум 1, максимум 5")
    improvements:str = Field(..., description="Предложения по улучшению (максимум 100 символов)")
    vacancy_price:str = Field(..., description="Цена за вакансию (максимум 100 символов)")
    resume_analysis_price:str = Field(..., description="Цена анализа резюме (максимум 100 символов)")
    free_comment:str|None