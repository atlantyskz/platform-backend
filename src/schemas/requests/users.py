# pylint: disable=all

import re

from pydantic import BaseModel, EmailStr, constr, field_validator


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=64)


    @field_validator("password")
    def password_must_contain_numbers(cls, v):
        if not re.search(r"[0-9]", v):
            raise ValueError("Пароль должен содержать цифры")
        return v

    @field_validator("password")
    def password_must_contain_uppercase(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Пароль должен содержать заглавные буквы")
        return v

    @field_validator("password")
    def password_must_contain_lowercase(cls, v):
        if not re.search(r"[a-z]", v):
            raise ValueError("Пароль должен содержать строчные буквы")
        return v



class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyEmailRequest(BaseModel):
    token: str

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr

class SetNewPassword(BaseModel):
    token: str
    new_password: str
