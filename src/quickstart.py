import streamlit as st
from langchain.llms import OpenAI
import yaml
import os

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



def quickstart_app():
    st.title("🦜🔗 Langchain Quickstart App")

    # Read API key from config file
    openai_api_key = load_config()
    print(f"OpenAI API Key  : {openai_api_key}, Type: {type(openai_api_key)}")

    with st.sidebar:
        if not openai_api_key:
            openai_api_key = st.text_input("OpenAI API Key", type="password")
            st.warning("No API key found in config file. Please enter it manually.")
        else:
            print(f"API Key: {openai_api_key}, Type: {type(openai_api_key)}")

            st.info("API key loaded from config file.")

    def generate_response(input_text):
        llm = OpenAI(temperature=0.7, openai_api_key=openai_api_key)
        st.info(llm(input_text))

    with st.form("my_form"):
        text = st.text_area("Enter text:", "What are 3 key advice for learning how to code?")
        submitted = st.form_submit_button("Submit")
        if not openai_api_key:
            st.info("Please add your OpenAI API key to continue.")
        elif submitted:
            generate_response(text)
