import os
from docx import Document
from PyPDF2 import PdfReader

def extract_text_from_file(uploaded_file):
    """Extract text from uploaded files (PDF, DOCX, TXT)."""
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        return "".join(page.extract_text() for page in reader.pages)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())
    elif uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8")
    else:
        raise ValueError("Unsupported file type")