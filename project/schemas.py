from pydantic import BaseModel

class StudentBase(BaseModel):
    name: str
    age: int
    grade: str

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: int
    parent_id: int
    class Config:
        orm_mode = True

class ParentBase(BaseModel):
    name: str
    phone: str
    email: str
    address: str

class ParentCreate(ParentBase):
    pass

class ParentResponse(ParentBase):
    id: int
    students: list[StudentResponse] = []
    class Config:
        orm_mode = True
