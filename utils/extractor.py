from pydantic import BaseModel
from typing import List
import google.generativeai as genai
from google.generativeai import types
import re

# 1. We keep our same Blueprint (Schema)
class ResumeData(BaseModel):
    name: str
    skills: List[str]
    job_titles: List[str]
    total_years_experience: int

def extract_resume_details(resume_text: str, api_key: str) -> ResumeData:
    """
    Sends the cleaned resume text to Gemini and forces it to return 
    the data formatted exactly like our ResumeData blueprint.
    """
    # Initialize the modern Gemini Client
    client = genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction="You are an expert HR assistant. Read the resume text and extract the required fields accurately."
    )
    
    # Define the configuration to enforce our Pydantic schema
    config = types.GenerationConfig(
        response_mime_type="application/json",
        response_schema=ResumeData,
        temperature=0.1 # Low temperature makes the AI more deterministic and accurate
    )

    # Call the lightweight, ultra-fast Gemini 2.5 Flash model
    response =model.generate_content(
        contents=resume_text,
        generation_config=config,
    )
    # Gemini returns a clean JSON string in response.text. 
    # We parse it directly back into our Pydantic structure.
    return ResumeData.model_validate_json(response.text)

def extract_real_title(job_link, fallback_title):
    """Attempts to extract the real job title from the URL based on the platform."""
    try:
        if "naukri.com/job-listings-" in job_link:
            url_path = job_link.split("job-listings-")[1].split("-")
            clean_words = []
            for word in url_path:
                if word.isdigit(): 
                    break
                clean_words.append(word)
            return " ".join(clean_words[:4]).title()
            
        elif "linkedin.com/jobs/view/" in job_link:
            # LinkedIn format: linkedin.com/jobs/view/unity-developer-at-company-12345
            url_path = job_link.split("jobs/view/")[1].split("?")[0].split("-")
            clean_words = []
            for word in url_path:
                # Stop if we hit a number or the word "at" (which precedes the company name)
                if word.isdigit() or word.lower() == "at":
                    break
                clean_words.append(word)
            return " ".join(clean_words[:4]).title()
            
        else:
            # For Indeed or any unknown portal, we safely use the fallback
            return fallback_title.title()
            
    except Exception:
        # If any parsing fails, never crash. Just return the fallback.
        return fallback_title.title()
    
def clean_text(text: str) -> str:
    # Replace multiple spaces or newlines with a single space
    cleaned = re.sub(r'\s+', ' ', text)
    return cleaned.strip()