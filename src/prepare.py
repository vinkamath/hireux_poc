import os
import dotenv
import json
import logging
from openai import OpenAI
from data_classes.candidate import Candidate
from data_classes.project import Project
from data_classes.utility import generate_prompt
from common.utility import write_dataclass_to_yaml
from google import genai

dotenv.load_dotenv()
client = OpenAI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger("ingest")


def process_portfolio(input_dir: str):
    """Processes the portfolio PDFs in the input directory."""

     # Configure the genai client with error handling
    try:
        client = genai.Client()
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return

    candidate_data = {}  # Dictionary to store all candidate related information.
    projects = []

    try:
        filenames = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]
    except FileNotFoundError:
        print(f"Error: Input directory '{input_dir}' not found.")
        return
    except Exception as e:
        print("Exception occurred: ", e)
        return

    for filename in filenames:
        filepath = os.path.join(input_dir, filename)
        file_parts = filename[:-4].split("_")  # Remove '.pdf' and split
        if len(file_parts) < 2:
            print(f"Skipping improperly formatted filename: {filename}")
            continue

        candidate_name = file_parts[0] # Extract the candidate name.
        page_type = file_parts[1].lower()

        if page_type == "home":
            continue  # Skip Home files

        try:
            my_file = client.files.upload(file=filepath) # No need for string literal 'file='
        except Exception as e:
            print("Exception in file upload", e)
            continue

        if page_type == "resume":
            prompt = generate_prompt(Candidate)
            dataclass_type = Candidate
        else:
            prompt = generate_prompt(Project)
            dataclass_type = Project

        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[prompt, my_file],
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': dataclass_type
                }
            )
            parsed_response = json.loads(response.text)

            if dataclass_type == Candidate:
                # candidate_data.update(parsed_response)  # Merge candidate info
                candidate_data = parsed_response # Store complete candidate data.
                candidate_data['name'] = candidate_name # Use the name from file.
            elif dataclass_type == Project:
                projects.append(parsed_response)

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for {filename}: {e}")
            print(f"Response text:\n{response.text}")
            continue
        except Exception as e:
            print(f"An unexpected error occurred processing {filename}: {e}")
            continue

    # Combine candidate data and projects
    candidate_data["projects"] = projects  # Add projects to candidate

    print(json.dumps(candidate_data, indent=4))



if __name__ == "__main__":

    process_portfolio("data/input/raw/AJain")