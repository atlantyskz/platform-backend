import uuid

from pydantic import BaseModel, validator

from src.core.exceptions import BadRequestException


class InterviewCommonQuestions(BaseModel):
    session_id: uuid.UUID
    question_text: str

    @validator('question_text')
    def question_text_validator(cls, value):
        if value == '':
            raise BadRequestException('Question text cannot be empty')
        return value


class InterviewCommonQuestionsUpdate(BaseModel):
    question_text: str

    @validator('question_text')
    def question_text_validator(cls, value):
        if value == '':
            raise BadRequestException('Question text cannot be empty')
        return value


class InterviewIndividualQuestions(BaseModel):
    session_id: uuid.UUID
    question_text: str
    resume_id: int

    @validator('question_text')
    def question_text_validator(cls, value):
        if value == '':
            raise BadRequestException('Question text cannot be empty')
        return value


class InterviewIndividualQuestionsUpdate(BaseModel):
    question_text: str

    @validator('question_text')
    def question_text_validator(cls, value):
        if value == '':
            raise BadRequestException('Question text cannot be empty')
        return value

