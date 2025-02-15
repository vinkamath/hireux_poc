import yaml
from dataclasses import asdict

def dataclass_to_yaml(data_object: object) -> str:
    """Converts a dataclass instance to a YAML string."""
    return yaml.dump(asdict(data_object), indent=2, sort_keys=False)

def write_dataclass_to_yaml(data_object: object, filepath: str) -> None:
    """Writes a dataclass instance to a YAML file."""
    yaml_string = dataclass_to_yaml(data_object)
    with open(filepath, 'w') as file:
        file.write(yaml_string)
