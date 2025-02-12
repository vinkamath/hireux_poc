import fitz  # PyMuPDF
import os
import openai
import dotenv
import json

dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF using PyMuPDF."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return None  # Return None if there's an error
    return text

def extract_portfolio_data_with_llm(text):
    """Extracts structured data from portfolio text using an LLM."""
    prompt = f"""
    You are an experienced rectuiter tasked with extracting structured data from UX designer portfolios and resumes.
    The input text contains information from a candidate's portfolio and/or resume.

    Extract the following information and return it as a JSON object:

    {{
      "candidate_name": "Candidate's Full Name",
      "portfolio_url": "URL of the candidate's online portfolio (if found, otherwise null)",
      "skills_and_experience": [
        "A list of the candidate's skills and experience, expressed as concise bullet points."
      ],
      "key_projects": [
        {{
          "project_name": "Name of the project",
          "problem": "Brief description of the problem the project addressed",
          "solution": "Brief description of the solution the candidate provided",
          "role": "The candidate's role in the project"
        }},
        ... (more projects)
      ]
    }}

    If any information is not found, set its value to null.  Do not make up information.

    Input Text:
    ```
    {text}
    ```
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # Or another suitable model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,  # Lower temperature for more deterministic output
            max_tokens=16000,  # Adjust as needed based on your input text length
        )

        # Parse the JSON response
        json_response = response.choices[0].message.content
        # Remove the ```json and ``` blocks, if present
        if json_response.endswith("```"):
            json_response = json_response[:-len("```")]
        if json_response.startswith("```json"):
            json_response = json_response[len("```json"):]
        return json.loads(json_response)
    except Exception as e:
        print(f"Error during LLM extraction: {e}")
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

        # --- LLM-BASED EXTRACTION ---
        structured_data = extract_portfolio_data_with_llm(combined_text)

        if structured_data:  # Proceed only if extraction was successful
            # --- FORMATTING FOR OUTPUT ---
            output_text = f"""Candidate Name: {structured_data.get('candidate_name', 'N/A')}
Portfolio URL: {structured_data.get('portfolio_url', 'N/A')}

Skills and Experience:
"""
            skills = structured_data.get('skills_and_experience', [])
            if skills:
              for skill in skills:
                  output_text += f"* {skill}\n"
            else:
              output_text+= "No skills extracted.\n"

            output_text += "\nKey Projects:\n"
            projects = structured_data.get('key_projects', [])
            if projects:
              for project in projects:
                  output_text += f"Project Name: {project.get('project_name', 'N/A')}\n"
                  output_text += f"  Problem: {project.get('problem', 'N/A')}\n"
                  output_text += f"  Solution: {project.get('solution', 'N/A')}\n"
                  output_text += f"  Role: {project.get('role', 'N/A')}\n\n"
            else:
                output_text += "No projects extracted.\n"

            output_file_path = os.path.join(output_dir, f"{candidate_name}_portfolio.txt")
            with open(output_file_path, "w", encoding="utf-8") as outfile:
                outfile.write(output_text)
            print(f"Processed {candidate_name} and saved to {output_file_path}")
        else:
            print(f"LLM extraction failed for {candidate_name}")


if __name__ == "__main__":
    input_pdf_directory = "data/input/raw/RHarris"
    output_text_directory = "data/input/portfolios"
    process_portfolio_pdfs(input_pdf_directory, output_text_directory)