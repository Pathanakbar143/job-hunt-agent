from pypdf import PdfReader
import re

def extract_text_from_pdf(path):

    reader = PdfReader(path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    return text

def clean_text(text: str) -> str:
    # Replace multiple spaces or newlines with a single space
    cleaned = re.sub(r'\s+', ' ', text)
    return cleaned.strip()