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
    def __init__(self, input_root_dir: str, output_dir: str):
        """Initialize OnboardPortfolios with input and output directories.

        Args:
            input_root_dir: Root directory containing portfolio subdirectories.
            output_dir: Directory for processed output
        """
        self.logger = logging.getLogger("ingest")
        self.input_root_dir = input_root_dir  
        self.output_dir = output_dir
        self.missing_resumes = []  

        # Initialize Gemini client
        try:
            self.client = genai.Client()
        except Exception as e:
            self.logger.error(f"Error configuring Gemini API: {e}")
            raise

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def create_structured_portfolio(self, input_dir: str):
        """Process all portfolio PDFs in the input directory."""
        self.input_dir = input_dir  

        # Local variables for each portfolio
        candidate_data = {}
        projects = []

        try:
            filenames = [f for f in os.listdir(self.input_dir) if f.endswith(".pdf")]
        except FileNotFoundError:
            self.logger.error(f"Error: Input directory '{self.input_dir}' not found.")
            return
        except Exception as e:
            self.logger.error(f"Exception occurred: {e}")
            return

        self.logger.info(f"Processing {len(filenames)} files in directory: {self.input_dir}")

        # Collect all project files first
        project_files = []
        resume_file = None

        for filename in filenames:
            filepath = os.path.join(self.input_dir, filename)
            file_parts = filename[:-4].split("_")  # Remove '.pdf' and split
            if len(file_parts) < 2:
                self.logger.info(f"Skipping improperly formatted filename: {filename}")
                continue

            page_type = file_parts[1].lower()

            if page_type in ("home", "aboutme"):
                self.logger.warning(f"Skipping Home/AboutMe file: {filename}")
                continue  # Skip Home files

            try:
                self.logger.info(f"Uploading file: {filename}")
                uploaded_file = self.client.files.upload(file=filepath)
                
                if page_type == "resume":
                    resume_file = uploaded_file
                else:
                    project_files.append(uploaded_file)
                    
            except Exception as e:
                self.logger.info("Exception in file upload", e)
                continue

        # Process resume first if available
        if resume_file:
            try:
                prompt = generate_prompt(Candidate)
                response = self.client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[prompt, resume_file],
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': Candidate
                    }
                )
                candidate_data = json.loads(response.text)
            except Exception as e:
                self.logger.info(f"Error processing resume: {e}")
                candidate_data = {}
        else:
            # Get candidate name from directory path
            candidate_name = os.path.basename(self.input_dir)
            self.logger.warning(f"No resume found for candidate: {candidate_name}")
            self.missing_resumes.append(candidate_name)

        # Process all project files
        projects = []
        for project_file in project_files:
            try:
                prompt = generate_prompt(Project)
                response = self.client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[prompt, project_file],
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': Project
                    }
                )
                parsed_response = json.loads(response.text)
                projects.append(parsed_response)
            except Exception as e:
                self.logger.info(f"Error processing project file: {e}")
                continue

        # Combine candidate data and projects
        candidate_data["projects"] = projects  # Add projects to candidate

        write_json_to_yaml(candidate_data, self.output_dir)

    def _get_portfolios(self) -> list:
        """Helper function to get all portfolio subdirectories."""
        portfolio_dirs = []
        try:
            for item in os.listdir(self.input_root_dir):
                item_path = os.path.join(self.input_root_dir, item)
                if os.path.isdir(item_path):
                    portfolio_dirs.append(item_path)
        except FileNotFoundError:
            self.logger.error(f"Error: Input root directory '{self.input_root_dir}' not found.")
            return []  # Return empty list if directory not found
        except Exception as e:
            self.logger.error(f"Exception occurred while listing directories: {e}")
            return []

        return portfolio_dirs

    def create_structured_portfolios(self):
        """Creates structured portfolios for all subdirectories in the input root directory."""
        portfolio_dirs = self._get_portfolios()
        if not portfolio_dirs:
            self.logger.warning(f"No portfolio directories found in '{self.input_root_dir}'.")
            return

        for portfolio_dir in portfolio_dirs:
            self.logger.info(f"Processing portfolio directory: {portfolio_dir}")
            self.create_structured_portfolio(portfolio_dir)

        # Print summary of missing resumes
        if self.missing_resumes:
            self.logger.warning("\nMissing resumes for the following candidates:")
            for candidate in self.missing_resumes:
                self.logger.warning(f"- {candidate}")


if __name__ == "__main__":
    onboarder = OnboardPortfolios("data/input/raw", "data/output/portfolio")  # Pass input root and output
    onboarder.create_structured_portfolios()