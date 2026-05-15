from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class ContactBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, examples=["John"])
    last_name: str = Field(..., min_length=1, max_length=50, examples=["Doe"])
    email: EmailStr = Field(..., examples=["john.doe@example.com"])
    phone: Optional[str] = Field(None, max_length=20, examples=["+1234567890"])
    birthday: Optional[date] = None
    additional_data: Optional[str] = Field(None, max_length=500)

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birthday: Optional[date] = None
    additional_data: Optional[str] = None

class ContactResponse(ContactBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=100)

class UserResponse(UserBase):
    id: int
    avatar: Optional[str]
    confirmed: bool = False
    role: str
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class RequestEmail(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=100)