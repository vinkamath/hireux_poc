from dataclasses import dataclass, field, fields
from typing import List, Optional, Dict, Any
import json

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
            "description": "A description of the problem the project was solving in 2-3 sentences.",
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

def generate_prompt_and_example(dataclass_type: type) -> tuple[str, str]:
    """Generates a prompt and example JSON for the dataclass."""

    prompt_parts = []
    example_data = {}

    for field_ in fields(dataclass_type):
        field_name = field_.name
        description = field_.metadata.get("description", "")
        prompt_instruction = field_.metadata.get("prompt_instruction", "")
        example = field_.metadata.get("example", None)
        allowed_values = field_.metadata.get("allowed_values", None)

        prompt_parts.append(f"*   `{field_name}`: {description} {prompt_instruction}")
        if allowed_values:
            prompt_parts.append(f"    Allowed values: {', '.join(allowed_values)}")

        if example is not None:
           if isinstance(example, str) and (example.startswith('[') or example.startswith('"')):
                try:
                    example_data[field_name] = json.loads(example)  # Parse JSON strings
                except json.JSONDecodeError:
                    example_data[field_name] = example #if parsing fails, store original
           else:
               example_data[field_name] = example
        elif field_.type == list or (hasattr(field_.type, '__origin__') and field_.type.__origin__ == list):
                example_data[field_name] = []  # Default for lists
        elif field_.type == Optional[List[str]]:
              example_data[field_name] = None #explicitly handle Optional[List]
        else:
            example_data[field_name] = None  # Default for other types


    prompt = (
        "Analyze the provided document, which contains a project case study, and structure the output as JSON, "
        "following this schema:\n\n" + "\n".join(prompt_parts) +
        "\n\nProvide a detailed analysis, filling in as many fields as possible based on the content of the document. "
        "Return *only* the JSON, nothing else."
    )
    example_json = json.dumps(example_data, indent=4)
    return prompt, example_json
# Generate prompt and example
prompt, example_json = generate_prompt_and_example(Project)
print("Prompt:\n", prompt)
print("\nExample JSON:\n", example_json)
