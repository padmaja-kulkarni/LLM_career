import streamlit as st
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from docx import Document


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


def file_upload_app():
    st.title("📄 Upload File and Use RAG")

    with st.sidebar:
        openai_api_key = st.text_input("OpenAI API Key", type="password")
        st.markdown("[Get an OpenAI API key](https://platform.openai.com/account/api-keys)")

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

        # Create RAG chain
        retriever = vectorstore.as_retriever()
        llm = OpenAI(temperature=0.7, openai_api_key=openai_api_key)
        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

        # Ask questions based on the uploaded file
        query = st.text_area("Ask a question based on the uploaded file:")
        if st.button("Get Answer"):
            if query.strip():
                try:
                    response = qa_chain.run(query)
                    st.success(response)
                except Exception as e:
                    st.error(f"Failed to generate a response: {str(e)}")
            else:
                st.warning("Please enter a question!")
    elif not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")


if __name__ == "__main__":
    file_upload_app()
