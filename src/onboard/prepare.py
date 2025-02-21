import os
import dotenv
import json
import logging
from data_classes.candidate import Candidate
from data_classes.project import Project
from data_classes.utility import generate_prompt
from common.utility import write_json_to_yaml
from google import genai

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger("ingest")


def process_portfolio(input_dir: str, output_dir: str):
    """Processes the portfolio PDFs in the input directory."""

     # Configure the genai client with error handling
    try:
        client = genai.Client()
    except Exception as e:
        logger.info(f"Error configuring Gemini API: {e}")
        return

    candidate_data = {}  # Dictionary to store all candidate related information.
    projects = []

    try:
        filenames = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]
    except FileNotFoundError:
        logger.info(f"Error: Input directory '{input_dir}' not found.")
        return
    except Exception as e:
        logger.info("Exception occurred: ", e)
        return
    logger.info(f"Processing {len(filenames)} files in directory: {input_dir}")

    for filename in filenames:
        filepath = os.path.join(input_dir, filename)
        file_parts = filename[:-4].split("_")  # Remove '.pdf' and split
        if len(file_parts) < 2:
            logger.info(f"Skipping improperly formatted filename: {filename}")
            continue

        candidate_name = file_parts[0] # Extract the candidate name.
        page_type = file_parts[1].lower()

        if page_type in ("home", "aboutme"):
            logger.warning(f"Skipping Home/AboutMe file: {filename}")
            continue  # Skip Home files

        try:
            logger.info(f"Uploading file: {filename}")
            my_file = client.files.upload(file=filepath) # No need for string literal 'file='
        except Exception as e:
            logger.info("Exception in file upload", e)
            continue

        if page_type == "resume":
            logger.info(f"Processing Resume file: {filename}")
            prompt = generate_prompt(Candidate)
            dataclass_type = Candidate
        else:
            logger.info(f"Processing Project file: {filename}")
            prompt = generate_prompt(Project)
            dataclass_type = Project

        try:
            logger.info(f"Generating content for file: {filename}")
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
            elif dataclass_type == Project:
                #logger.info(json.dumps(parsed_response, indent=4))
                projects.append(parsed_response)

        except json.JSONDecodeError as e:
            logger.info(f"Error parsing JSON for {filename}: {e}")
            logger.info(f"Response text:\n{response.text}")
            continue
        except Exception as e:
            logger.info(f"An unexpected error occurred processing {filename}: {e}")
            continue

    # Combine candidate data and projects
    candidate_data["projects"] = projects  # Add projects to candidate

    write_json_to_yaml(candidate_data, output_dir)   



if __name__ == "__main__":

    process_portfolio("data/input/raw/AKhomutov", "data/output/portfolio")