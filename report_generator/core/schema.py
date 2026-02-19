from typing import List, Optional
from pydantic import BaseModel


# -------------------------------
# Базовая информация (повторяется для каждой работы)
# -------------------------------
class University(BaseModel):
    name: str
    abbr: Optional[str]
    faculty: Optional[str]
    department: Optional[str]


class Student(BaseModel):
    name: str
    direction: Optional[str]
    direction_name: Optional[str]
    profile: Optional[str]


class Teacher(BaseModel):
    name: str
    position: Optional[str]


class Location(BaseModel):
    city: str
    year: int


# -------------------------------
# Содержание лабораторной
# -------------------------------
class ImageData(BaseModel):
    number: int
    src: str
    alt: Optional[str]
    caption: Optional[str]
    max_width: Optional[str]


class Step(BaseModel):
    text: str
    images: Optional[List[ImageData]] = []


class Question(BaseModel):
    question: str
    answer: str


class LabInfo(BaseModel):
    number: int
    discipline: str
    theme: str


class LabContent(BaseModel):
    lab: LabInfo
    goals: Optional[str]
    procedure: List[Step]
    questions: Optional[List[Question]] = []
    conclusion: Optional[str]


# -------------------------------
# Полная модель отчёта
# -------------------------------
class LabReport(BaseModel):
    university: University
    student: Student
    teacher: Teacher
    location: Location
    content: LabContent
