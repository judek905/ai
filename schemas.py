import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class GenerateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=50)


class PaymentRequestIn(BaseModel):
    payer_phone: str

    @field_validator("payer_phone")
    @classmethod
    def valid_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "")
        if not re.fullmatch(r"(\+256|0)7\d{8}", v):
            raise ValueError("Enter a valid Uganda mobile number, e.g. 0770000000")
        return v
