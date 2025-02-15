import fitz  # PyMuPDF
import os
from openai import OpenAI
import dotenv
import json
import logging
from template.data_classes import Candidate
from common.utility import write_dataclass_to_yaml

dotenv.load_dotenv()
client = OpenAI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger("ingest")


def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF using PyMuPDF."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        logger.info(f"Error processing {pdf_path}: {e}")
        return None  # Return None if there's an error
    return text

def extract_portfolio_data_with_llm(text):
    """Extracts structured data from portfolio text using an LLM."""

    prompt = f"""
    You are an experienced rectuiter tasked with extracting structured data from UX designer portfolios and resumes.
    Please summarize the candidate's portfolio accurately. Do not make up any information. If you are unsure about any field, leave it empty.
    Input Text:
    ```
    {text}
    ```
    """
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-o3-mini",  
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,  # Lower temperature for more deterministic output
            max_tokens=16000,  # Adjust as needed based on your input text length
            response_format=Candidate  # Use the Candidate dataclass for structured output
        )

        # Parse the JSON response
        json_response = completion.choices[0].message.content
        return json.loads(json_response)
    except Exception as e:
        logger.info(f"Error during LLM extraction: {e}")
        return None


def process_portfolio_pdfs(input_dir, output_dir):
    """Processes PDFs, extracts text, uses LLM for structured data, and saves."""

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    candidate_files = {}
    for filename in os.listdir(input_dir):
        if filename.endswith(".pdf"):
            candidate_name = filename.split('_')[0]
            if candidate_name not in candidate_files:
                candidate_files[candidate_name] = []
            candidate_files[candidate_name].append(os.path.join(input_dir, filename))

    for candidate_name, pdf_paths in candidate_files.items():
        combined_text = ""
        for pdf_path in pdf_paths:
            text = extract_text_from_pdf(pdf_path)
            if text:
                combined_text += text + "\n\n"
            else:
                logger.info(f"Failed to extract text from {pdf_path}")
                continue

        # --- LLM-BASED EXTRACTION ---
        structured_data = extract_portfolio_data_with_llm(combined_text)

        if structured_data:  # Proceed only if extraction was successful
            output_file_path = os.path.join(output_dir, f"{candidate_name}_portfolio.txt")
            write_dataclass_to_yaml(structured_data, output_file_path)
            logger.info(f"Processed {candidate_name} and saved to {output_file_path}")
        else:
            logger.info(f"LLM extraction failed for {candidate_name}")


if __name__ == "__main__":
    input_pdf_directory = "data/input/raw/AJain"
    output_text_directory = "data/input/portfolios"
    process_portfolio_pdfs(input_pdf_directory, output_text_directory)