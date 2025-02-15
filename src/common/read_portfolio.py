import yaml

def load_candidate_data(filepath):
    """Loads candidate data from a YAML file.

    Args:
        filepath: The path to the YAML file.

    Returns:
        A dictionary representing the candidate data, or None on error.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:  # Use UTF-8 encoding
            data = yaml.safe_load(f)
            return data
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        return None

def print_candidate_info(data):
    """Prints formatted candidate information."""
    if not data:
        return

    print(f"Candidate Name: {data['candidate']['name']}")
    print(f"Portfolio URL: {data['candidate']['portfolio_url']}")
    print("\nSkills and Experience:")
    for category, skills in data['skills_and_experience'].items():
        print(f"  {category.title().replace('_', ' ')}:")  # Nicer formatting
        for skill in skills:
            print(f"    - {skill}")

    print("\nProjects:")
    for project in data['projects']:
        print(f"  Project Name: {project['name']}")
        print(f"    Problem: {project['problem']}")
        print(f"    Solution: {project['solution']}")
        print(f"    Role: {project['role']}")
        if 'impact' in project:  # Handle optional fields
            print(f"    Impact: {project['impact']}")
        print("-" * 20)

def get_project_names(data):
    """Extracts a list of project names."""
    return [project['name'] for project in data['projects']]

def get_skills_by_category(data, category):
    """Gets skills for a given category."""
    return data['skills_and_experience'].get(category, [])


# Example usage:
filepath = "candidate_data.yaml"  # Or wherever you save the file
candidate_data = load_candidate_data(filepath)

if candidate_data:
    print_candidate_info(candidate_data)

    project_names = get_project_names(candidate_data)
    print(f"\nProject Names: {project_names}")

    interaction_design_skills = get_skills_by_category(candidate_data, 'interaction_design')
    print(f"\nInteraction Design Skills: {interaction_design_skills}")

    #Chunking by section
    print("\nChunking by Skills and Experience Section")
    for category, skills in candidate_data['skills_and_experience'].items():
      print(f"\n  {category.title().replace('_', ' ')}:")  # Nicer formatting
      chunk = "\n".join([f"    - {skill}" for skill in skills])
      print(chunk)
else:
    print("Failed to load candidate data.")