from dataclasses import dataclass, field
from typing import List

@dataclass
class Project:
    """
    Represents a simplified project case study.
    """

    name: str = field(
        metadata={
            "description": "The name of the project.",
            "example": '"Project Phoenix"',
        }
    )
    role: str = field(
        metadata={
            "description": "The candidate's role in the project.",
            "example": '"UX Designer"',
        }
    )
    problem_description: str = field(
        metadata={
            "description": "A description of the problem the project was solving.",
            "example": '"Users were experiencing difficulty navigating the existing website."',
        }
    )
    solution_description: str = field(
        metadata={
            "description": "A description of the solution implemented.",
            "example": '"A redesigned website with improved information architecture and user flows."',
        }
    )
    process: List[str] = field(
        default_factory=list,
        metadata={
            "description": "A list of processes followed during the project.",
            "allowed_values": [
                "User / customer problem",
                "User / customers needs",
                "User / customer pain points",
                "User / customer journey mapping",
                "User flows",
                "Wireframes",
                "User Testing",
                "Iterations",
                "Prototypes",
                "Outcome",
            ],
            "prompt_instruction": "Select one or more from the allowed values. Use an empty list [] if none are mentioned.",
            "example": '["User flows", "Wireframes", "User Testing"]',
        },
    )
    outcome: List[str] = field(
        default_factory=list, # Default to an empty list
        metadata={
            "description": "The type(s) of outcome produced.",
            "allowed_values": ["Website", "Mobile App", "Web app", "Devices", "Other"],
             "prompt_instruction": "Select one or more from the allowed values. Use an empty list [] if none are specified.",
            "example": '["Website", "Mobile App"]',
        },
    )
    software_or_tools_used: List[str] = field(
        default_factory=list,
        metadata={
            "description": "A list of software or tools used in the project.",
            "prompt_instruction": "Provide a list of strings, or null if not specified.",
            "example": '["Figma", "Adobe XD"]',
        },
    )


