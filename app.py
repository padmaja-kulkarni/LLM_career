import streamlit as st
from utils.database_utils import create_database, save_progress, get_progress
import speech_recognition as sr
from utils.llm_utils import load_config
from utils.file_processing import extract_text_from_file
from utils.llm_utils import customize_resume
from utils.llm_utils import generate_mock_questions, parse_questions, evaluate_answer


def record_audio():
    """Capture audio input and convert it to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Please speak into the microphone.")
        try:
            audio = recognizer.listen(source, timeout=10)
            text = recognizer.recognize_google(audio)
            st.success("Audio captured successfully!")
            return text
        except sr.UnknownValueError:
            st.error("Could not understand the audio. Please try again.")
        except sr.RequestError as e:
            st.error(f"Could not request results from the speech recognition service; {e}")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    return ""


def interview_preparation(api_key):
    st.header("Interview Preparation")
    job_title = st.text_input("Enter Job Title:")

    if st.button("Generate Mock Questions"):
        generated_text = generate_mock_questions(job_title, api_key)
        behavioral_questions, technical_questions = parse_questions(generated_text)

        if behavioral_questions:
            st.subheader("Behavioral Questions")
            for i, question in enumerate(behavioral_questions):
                st.write(f"{i + 1}. {question}")
            st.session_state.behavioral_questions = behavioral_questions

        if technical_questions:
            st.subheader("Technical Questions")
            for i, question in enumerate(technical_questions):
                st.write(f"{i + 1}. {question}")
            st.session_state.technical_questions = technical_questions

    # Handle answer submission
    for question_set, label in zip(
            [st.session_state.get("behavioral_questions", []), st.session_state.get("technical_questions", [])],
            ["Behavioral", "Technical"]
    ):

        for i, question in enumerate(question_set):
            st.write(f"Q{i + 1}: {question}")

            # Create side-by-side buttons
            cols = st.columns(2)
            with cols[0]:
                record_clicked = st.button(f"Record Answer for Q{i + 1}", key=f"record_{i}_{label}")
            with cols[1]:
                submit_clicked = st.button(f"Submit Answer for Q{i + 1}", key=f"submit_{i}_{label}")

            user_answer = ""
            if record_clicked:
                user_answer = record_audio()
                st.text_area(f"Your Recorded Answer for Q{i + 1}:", user_answer, key=f"recorded_answer_{i}_{label}")
            else:
                user_answer = st.text_area(f"Your Answer for Q{i + 1}:", key=f"answer_{i}_{label}")

            if submit_clicked:
                feedback = evaluate_answer(question, user_answer, api_key)
                st.text_area(f"Feedback for Q{i + 1}:", feedback)

                # Parse score from feedback (if included)
                score = int(feedback.split("Score: ")[-1].split("/")[0]) if "Score:" in feedback else None
                save_progress(question, user_answer, feedback, score)




def main():
    st.title("Job Application Helper with Voice Input")
    st.sidebar.title("Navigation")
    section = st.sidebar.radio("Choose Section", ["Resume Customization", "Interview Preparation"])
    api_key = load_config()
    if not api_key:
        st.sidebar.text_input("OpenAI API Key", type="password")

    if not api_key:
        st.warning("Please provide your OpenAI API Key to proceed.")
        return

    if section == "Interview Preparation":
        interview_preparation(api_key)

    if section == "Resume Customization":
        st.header("Resume Customization")

        # Job Description Input
        job_description = st.text_area("Enter Job Description:", height=150)

        # File Upload
        uploaded_file = st.file_uploader("Upload Resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
        if uploaded_file:
            resume_content = extract_text_from_file(uploaded_file)
            st.text_area("Uploaded Resume Content:", resume_content, height=150)

            if st.button("Customize Resume"):
                customized_resume = customize_resume(job_description, resume_content, api_key)
                st.text_area("Customized Resume:", customized_resume, height=300)


if __name__ == "__main__":
    create_database()  # Ensure database is created
    main()
