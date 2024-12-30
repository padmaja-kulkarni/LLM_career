from langchain.chat_models import ChatOpenAI
import os
import yaml

import re

def parse_questions(generated_text):
    """Extract questions using regex."""
    behavioral_section = re.search(r"Behavioral Questions:(.*?)- Technical Questions:", generated_text, re.DOTALL)
    technical_section = re.search(r"- Technical Questions:(.*)", generated_text, re.DOTALL)

    behavioral_questions = []
    technical_questions = []

    if behavioral_section:
        behavioral_questions = re.findall(r"\d+\.\s+(.*)", behavioral_section.group(1))

    if technical_section:
        technical_questions = re.findall(r"\d+\.\s+(.*)", technical_section.group(1))

    return behavioral_questions, technical_questions


def load_config(file_name="config.yaml"):
    """
    Load configuration file from the 'config/' directory, relative to the project root.
    """
    # Determine the project root dynamically
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Build the path to the config file
    config_path = os.path.join(project_root, "config", file_name)

    try:
        with open(config_path, "r") as file:
            return yaml.safe_load(file)['openai_api_key']
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

def customize_resume(job_description, resume_content, api_key):
    """Generate customized resume using LLM."""
    llm = ChatOpenAI(model_name="gpt-4", openai_api_key=api_key)
    prompt = f"""
    You are a professional career advisor. 
    Based on the job description below, customize the resume to align with it:

    Job Description:
    {job_description}

    Candidate's Resume:
    {resume_content}

    Provide a revised version of the resume.
    """
    return llm.predict(prompt)


def generate_mock_questions(job_title, api_key):
    """Generate mock interview questions with structured formatting."""
    llm = ChatOpenAI(model_name="gpt-4", openai_api_key=api_key)
    prompt = f"""
    Generate a set of mock interview questions for the role: {job_title}.
    Format the questions as follows:
    - Behavioral Questions:
      1. [Question]
      2. [Question]
      3. [Question]
    - Technical Questions:
      1. [Question]
      2. [Question]
    """
    return llm.predict(prompt)

def evaluate_answer(question, answer, api_key):
    """Evaluate the user's answer and provide feedback."""
    llm = ChatOpenAI(model_name="gpt-4", openai_api_key=api_key)
    prompt = f"""
    Evaluate the following answer to the question and provide feedback with a score out of 10:

    Question: {question}
    Answer: {answer}

    Provide feedback and suggestions for improvement.
    """
    return llm.predict(prompt)

