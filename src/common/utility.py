import yaml
import logging
import os
from dataclasses import asdict

logger = logging.getLogger("common.utility")

def dataclass_to_yaml(data_object: object) -> str:
    """Converts a dataclass instance to a YAML string."""
    return yaml.dump(asdict(data_object), indent=2, sort_keys=False)

def write_dataclass_to_yaml(data_object: object, filepath: str) -> None:
    """Writes a dataclass instance to a YAML file."""
    yaml_string = dataclass_to_yaml(data_object)
    with open(filepath, 'w') as file:
        file.write(yaml_string)

def write_json_to_yaml(data_object: dict, output_dir: str) -> None:
    """Writes a JSON object to a YAML file."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    yaml_string = yaml.dump(data_object, indent=2, sort_keys=False)
    try:
        candidate_name = data_object['name']
    except KeyError:
        logging.error("Candidate name not found in data object.")
        raise KeyError("Candidate name not found in data object.")
    candidate_name = candidate_name.lower().replace(" ", "_")
    with open(f"{output_dir}/{candidate_name}.yaml", 'w') as file:
        file.write(yaml_string)