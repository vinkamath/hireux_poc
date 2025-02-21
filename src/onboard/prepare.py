import os
import dotenv
import json
import logging
from src.data_classes.candidate import Candidate
from src.data_classes.project import Project
from src.data_classes.utility import generate_prompt
from src.common.utility import write_json_to_yaml
from google import genai

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')


class OnboardPortfolios:
    def __init__(self, input_dir: str, output_dir: str):
        """Initialize OnboardPortfolios with input and output directories.
        
        Args:
            input_dir: Directory containing portfolio PDFs
            output_dir: Directory for processed output
        """
        # Configure logging
        self.logger = logging.getLogger("ingest")
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.candidate_data = {}
        self.projects = []
        
        # Initialize Gemini client
        try:
            self.client = genai.Client()
        except Exception as e:
            self.logger.error(f"Error configuring Gemini API: {e}")
            raise
            
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
    def create_structured_portfolio(self):
        """Process all portfolio PDFs in the input directory."""
        try:
            filenames = [f for f in os.listdir(self.input_dir) if f.endswith(".pdf")]
        except FileNotFoundError:
            self.logger.error(f"Error: Input directory '{self.input_dir}' not found.")
            return
        except Exception as e:
            self.logger.error(f"Exception occurred: {e}")
            return

        self.logger.info(f"Processing {len(filenames)} files in directory: {self.input_dir}")

        for filename in filenames:
            filepath = os.path.join(self.input_dir, filename)
            file_parts = filename[:-4].split("_")  # Remove '.pdf' and split
            if len(file_parts) < 2:
                self.logger.info(f"Skipping improperly formatted filename: {filename}")
                continue

            candidate_name = file_parts[0] # Extract the candidate name.
            page_type = file_parts[1].lower()

            if page_type in ("home", "aboutme"):
                self.logger.warning(f"Skipping Home/AboutMe file: {filename}")
                continue  # Skip Home files

            try:
                self.logger.info(f"Uploading file: {filename}")
                my_file = self.client.files.upload(file=filepath) # No need for string literal 'file='
            except Exception as e:
                self.logger.info("Exception in file upload", e)
                continue

            if page_type == "resume":
                self.logger.info(f"Processing Resume file: {filename}")
                prompt = generate_prompt(Candidate)
                dataclass_type = Candidate
            else:
                self.logger.info(f"Processing Project file: {filename}")
                prompt = generate_prompt(Project)
                dataclass_type = Project

            try:
                self.logger.info(f"Generating content for file: {filename}")
                response = self.client.models.generate_content(
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
                    self.candidate_data = parsed_response # Store complete candidate data.
                elif dataclass_type == Project:
                    #logger.info(json.dumps(parsed_response, indent=4))
                    self.projects.append(parsed_response)

            except json.JSONDecodeError as e:
                self.logger.info(f"Error parsing JSON for {filename}: {e}")
                self.logger.info(f"Response text:\n{response.text}")
                continue
            except Exception as e:
                self.logger.info(f"An unexpected error occurred processing {filename}: {e}")
                continue

        # Combine candidate data and projects
        self.candidate_data["projects"] = self.projects  # Add projects to candidate

        write_json_to_yaml(self.candidate_data, self.output_dir)   



if __name__ == "__main__":
    onboarder = OnboardPortfolios("data/input/raw/AKhomutov", "data/output/portfolio")
    onboarder.create_structured_portfolio()