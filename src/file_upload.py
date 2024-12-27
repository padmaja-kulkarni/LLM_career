import os
import streamlit as st
from docx import Document
from PyPDF2 import PdfReader
from langchain.chat_models import ChatOpenAI
import yaml


def load_config(file_name="config.yaml"):
    """
    Load configuration file from the 'config/' directory, relative to the project root.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config", file_name)

    try:
        with open(config_path, "r") as file:
            return yaml.safe_load(file)['openai_api_key']
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at {config_path}")


def load_file(uploaded_file):
    """
    Load uploaded files into text format.
    Supports PDF, DOCX, and TXT files.
    """
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        text = "".join([page.extract_text() for page in reader.pages])
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
    elif uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")
    else:
        raise ValueError("Unsupported file type")
    return text


def process_combined_files_with_job_content():
    st.title("Multi-File Analysis with Optional Job Content and Custom Questions")

    openai_api_key = load_config()

    with st.sidebar:
        if not openai_api_key:
            openai_api_key = st.text_input("OpenAI API Key", type="password")
            st.warning("No API key found in config file. Please enter it manually.")
        else:
            st.info("API key loaded from config file.")

    uploaded_files = st.file_uploader("Upload Files (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], accept_multiple_files=True)

    job_content = st.text_area("Enter Job Content (Optional):", height=150)

    if uploaded_files and openai_api_key:
        st.info("Processing all uploaded files together...")

        combined_text = ""
        for uploaded_file in uploaded_files:
            try:
                file_text = load_file(uploaded_file)
                combined_text += f"\n\n--- Content from {uploaded_file.name} ---\n\n{file_text}"
            except Exception as e:
                st.error(f"Failed to load file '{uploaded_file.name}': {str(e)}")

        if combined_text:
            st.success("All files successfully loaded!")
            st.text_area("Combined Content from All Files:", combined_text, height=100)

            user_question = st.text_area("Ask a question about the content:", height=100)

            if st.button("Get Answer"):
                llm = ChatOpenAI(model_name='gpt-4', openai_api_key=openai_api_key)

                try:
                    # Prepare the prompt
                    prompt = f"Using the following combined content, answer the user's question."
                    if job_content.strip():
                        prompt += f"\n\nJob Content:\n{job_content}"
                    prompt += f"\n\nCombined Content from Files:\n{combined_text}\n\nQuestion: {user_question}"

                    # Generate response
                    response = llm.predict(prompt)

                    st.text_area("Answer:", response, height=300)
                except Exception as e:
                    st.error(f"Failed to generate response: {str(e)}")

    elif not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")


if __name__ == "__main__":
    process_combined_files_with_job_content()
