import os
import streamlit as st
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from docx import Document
import yaml

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

def load_file(uploaded_file):
    """
    Load uploaded files into a LangChain-compatible loader.
    Supports PDF, DOCX, and TXT files.
    """
    if uploaded_file.type == "application/pdf":
        # Save PDF temporarily and load it
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        loader = PyPDFLoader("temp.pdf")
        documents = loader.load()
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        # Process DOCX file
        doc = Document(uploaded_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
        documents = [{"content": text, "metadata": {}}]
    elif uploaded_file.type == "text/plain":
        # Process plain text file
        text = uploaded_file.read().decode("utf-8")
        documents = [{"content": text, "metadata": {}}]
    else:
        raise ValueError("Unsupported file type")
    return documents


def file_upload_app_rag():
    st.title("📄 Upload File and Use RAG")

    # Read API key from config file
    openai_api_key = load_config()

    with st.sidebar:
        if not openai_api_key:
            openai_api_key = st.text_input("OpenAI API Key", type="password")
            st.warning("No API key found in config file. Please enter it manually.")
        else:
            st.info("API key loaded from config file.")

    uploaded_file = st.file_uploader("Upload a file (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

    if uploaded_file and openai_api_key:
        st.info("Processing the file...")

        try:
            # Load and process the uploaded file
            documents = load_file(uploaded_file)
            st.success("File successfully loaded!")
        except Exception as e:
            st.error(f"Failed to load file: {str(e)}")
            return

        # Embed documents and set up vector store
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        vectorstore = FAISS.from_documents(documents, embeddings)

        # Save vectorstore to disk (optional, for reuse)
        vectorstore.save_local("local_vectorstore")

        # Load vectorstore from disk (for demonstration of persistence)
        vectorstore = FAISS.load_local("local_vectorstore", embeddings, allow_dangerous_deserialization=True)

        # Create RAG chain
        retriever = vectorstore.as_retriever(search_kwargs={"k": 1})  # Reduce the number of retrieved chunks
        llm = OpenAI(temperature=0.7, max_tokens=150, openai_api_key=openai_api_key)  # Limit response length

        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

        # Ask questions based on the uploaded file
        query = st.text_area("Ask a question based on the uploaded file:")
        if st.button("Get Answer"):
            if query.strip():
                try:
                    retrieved_docs = retriever.get_relevant_documents(query)
                    # Combine and clean retrieved content
                    combined_content = " ".join([doc.page_content for doc in retrieved_docs])

                    # Add structured context for LLM
                    structured_prompt = f"""
                    Based on the following CV information:
                    {combined_content}

                    {query}
                    """
                    st.text_area("Debug Prompt", structured_prompt)

                    response = qa_chain.run(structured_prompt)
                    st.success(response)
                except Exception as e:
                    st.error(f"Failed to generate a response: {str(e)}")
            else:
                st.warning("Please enter a question!")
    elif not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")


if __name__ == "__main__":
    file_upload_app_rag()
