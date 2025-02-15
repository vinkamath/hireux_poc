from dataclasses import dataclass
from typing import List, Optional
from pydantic import BaseModel

@dataclass
class Bio:
    name: str
    portfolio_url: str
    location: str = None

@dataclass
class SkillSet:
    skill: List[str]
    tools: List[str]

@dataclass
class Education:
    degree: str
    institution: str
    graduation_year: int
    GPA: Optional[float] = None

@dataclass
class Experience:
    company: str
    title: str
    location: str
    start_date: str
    end_date: str
    description: str 

@dataclass
class Project:
    name: str
    problem: str
    solution: str
    role: str

@dataclass
class Candidate(BaseModel):
    bio: Bio
    skillset: SkillSet
    education: List[Education]
    experience: List[Experience]
    projects: List[Project]