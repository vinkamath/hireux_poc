from dataclasses import dataclass, field
from typing import List, Optional
from .project import Project

@dataclass
class Experience:
    company: str = field(metadata={"description": "The company name.", "example": '"Acme Corp"'})
    title: str = field(metadata={"description": "The job title.", "example": '"Software Engineer"'})
    location: str = field(metadata={"description": "The location of the job.", "example": '"New York, NY"'})
    start_date: str = field(metadata={"description": "The start date of the job (YYYY-MM).", "example": '"2022-06"'})
    end_date: str = field(metadata={"description": "The end date of the job (YYYY-MM).  Use Present if currently employed.", "example": '"2023-12"'})
    description: str = field(metadata={"description": "A description of the responsibilities and achievements.", "example": '"Led a team of developers..."'})

@dataclass
class Education:
    degree: str = field(metadata={"description": "The degree earned.", "example": '"B.S. Computer Science"'})
    institution: str = field(metadata={"description": "The institution name.", "example": '"University of California, Berkeley"'})
    graduation_year: int = field(metadata={"description": "The year of graduation.", "example": "2020"})
    gpa: Optional[float] = field(metadata={"description": "The GPA.", "example": "3.8"})
  

@dataclass
class Candidate:
    """
    Represents a candidate's information.
    """

    name: str = field(
        metadata={
            "description": "The candidate's name.",
            "example": '"John Smith"'}
    )
    email: str = field(
        metadata={
            "description": "The candidate's email address.", 
            "example": '"john.smith@example.com"'}
    )
    phone: str = field(
        metadata={
            "description": "The candidate's phone number.",
            "example": '"+1-555-123-4567"'}
    )
    linkedin: str = field(
        metadata={
            "description": "The candidate's LinkedIn profile URL.",
            "example": '"https://www.linkedin.com/in/abhishekjain/"'},
    )
    github: str = field(
        metadata={
            "description": "The candidate's GitHub profile URL.", 
            "example": '"https://github.com/abhishekjain"'}
    )
    portfolio: str = field(
        metadata={
            "description": "The candidate's portfolio website URL.",
            "example": '"https://www.abhishekjain.com"'},
    )
    skills: List[str] = field(
        default_factory=list,
        metadata={
            "description": "A list of the candidate's skills.",
            "example": '["UX Design", "UI Design", "User Research", "Prototyping"]',
        },
    )
    experience: List[Experience] = field(
        default_factory=list,
        metadata={"description": "A list of the candidate's work experiences."}
    )
    education: List[Education] = field(
        default_factory=list,
        metadata={"description": "A list of the candidate's educational background."}
    )
    tools: List[str] = field(
        default_factory=list,
        metadata={
            "description": "A list of tools and technologies the candidate is proficient with.",
            "example": '["Figma", "Adobe Creative Suite", "Jira", "Confluence"]'
        }
    )
    projects: List[Project] = field(
        default_factory=list,
        metadata={"description": "A list of projects the candidate has worked on. Always return null"}  # This will be populated separately
    )