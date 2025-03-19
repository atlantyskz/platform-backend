from pydantic import BaseModel


class InterviewQuestionsSchema(BaseModel):
    id: int
    question_text: str
