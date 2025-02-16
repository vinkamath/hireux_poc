import json
from typing import List, Optional
from dataclasses import fields

def generate_prompt(dataclass_type: type) -> str:
    """Generates a prompt string for the given dataclass."""
    prompt_parts = []
    for field_ in fields(dataclass_type):
        field_name = field_.name
        description = field_.metadata.get("description", "")
        prompt_instruction = field_.metadata.get("prompt_instruction", "")
        allowed_values = field_.metadata.get("allowed_values", None)

        prompt_parts.append(f"*   `{field_name}`: {description} {prompt_instruction}")
        if allowed_values:
            prompt_parts.append(f"    Allowed values: {', '.join(allowed_values)}")
    
    prompt = (
        "Analyze the provided document, which contains a project case study, and structure the output as JSON, "
        "following this schema:\n\n" + "\n".join(prompt_parts) +
        "\n\nProvide a detailed analysis, filling in as many fields as possible based on the content of the document. "
        "Return *only* the JSON, nothing else."
    )
    return prompt

def generate_example(dataclass_type: type) -> dict:
    """Generates an example JSON dict for the given dataclass."""
    example_data = {}
    for field_ in fields(dataclass_type):
        field_name = field_.name
        example = field_.metadata.get("example", None)
        
        if example is not None:
            if isinstance(example, str) and (example.startswith('[') or example.startswith('"')):
                try:
                    example_data[field_name] = json.loads(example)  # Parse JSON strings
                except json.JSONDecodeError:
                    example_data[field_name] = example  # if parsing fails, store original
            else:
                example_data[field_name] = example
        elif field_.type == list or (hasattr(field_.type, '__origin__') and field_.type.__origin__ == list):
            example_data[field_name] = []  # Default for lists
        elif field_.type == Optional[List[str]]:
            example_data[field_name] = None  # explicitly handle Optional[List]
        else:
            example_data[field_name] = None  # Default for other types
    return example_data
