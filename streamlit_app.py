import streamlit as st
from src.quickstart import quickstart_app
from src.file_upload import process_combined_files_with_job_content

# Set up navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Go to", ["Quickstart App", "Upload & RAG"])

# Display the selected app
if app_mode == "Quickstart App":
    quickstart_app()
elif app_mode == "Upload & RAG":
    process_combined_files_with_job_content()