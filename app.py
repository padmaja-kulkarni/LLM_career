import streamlit as st
from utils.database_utils import create_database, save_progress, get_progress
import speech_recognition as sr
from utils.llm_utils import load_config
from utils.file_processing import extract_text_from_file
from utils.llm_utils import customize_resume
from utils.llm_utils import generate_mock_questions, parse_questions, evaluate_answer
from utils.voice_utils import record_audio_segment

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
def custom_interview_prep(api_key):
    st.header("Custom Interview Preparation")

    job_title = st.text_input("Enter Job Title:")

    # Initialize session state for questions
    if "custom_questions" not in st.session_state:
        st.session_state.custom_questions = [{
            "question": "",
            "answer": "",
            "feedback": "",
        }]

    # Display the initial question input section
    for idx, q_data in enumerate(st.session_state.custom_questions):
        st.subheader(f"Question {idx + 1}")
        question = st.text_area(
            "Enter or Edit Question:",
            value=q_data["question"],
            key=f"custom_question_{idx}",
            height=100
        )

        # Update session state with the new question value
        st.session_state.custom_questions[idx]["question"] = question

        # Record audio or input text for answers
        cols = st.columns(2)
        with cols[0]:
            record_clicked = st.button(f"Record Answer for Q{idx + 1}", key=f"record_{idx}")
        with cols[1]:
            submit_clicked = st.button(f"Submit Answer for Q{idx + 1}", key=f"submit_{idx}")

        if record_clicked:
            recorded_text = record_audio()
            st.session_state.custom_questions[idx]["answer"] += f" {recorded_text}".strip()

        # Input for the answer
        answer = st.text_area(
            f"Your Answer for Q{idx + 1}:",
            value=st.session_state.custom_questions[idx]["answer"],
            key=f"answer_{idx}",
            height=100
        )

        # Update session state with the answer value
        st.session_state.custom_questions[idx]["answer"] = answer

        # Submit answer and get feedback
        if submit_clicked:
            if answer.strip():
                feedback = evaluate_answer(question, answer, api_key)
                st.session_state.custom_questions[idx]["feedback"] = feedback
                st.text_area(f"Feedback for Q{idx + 1}:", feedback, height=100)

                # Save progress
                save_progress(question, answer, feedback, score=None)
            else:
                st.warning("Please provide an answer before submitting.")

    # Add a button to insert a new question
    if st.button("Add Another Question", key="add_question"):
        st.session_state.custom_questions.append({
            "question": "",
            "answer": "",
            "feedback": "",
        })
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

            # Initialize the answer in session state
            if f"combined_answer_{i}_{label}" not in st.session_state:
                st.session_state[f"combined_answer_{i}_{label}"] = ""

            # Handle "Record Answer" functionality
            if record_clicked:
                recorded_text = record_audio()
                # Append recorded text to the current text in the box
                st.session_state[f"combined_answer_{i}_{label}"] += f" {recorded_text}".strip()

            # Ensure the session state is initialized only once
            if f"combined_answer_{i}_{label}" not in st.session_state:
                st.session_state[f"combined_answer_{i}_{label}"] = ""

            # Display the text area without directly passing session state as `value`
            combined_answer = st.text_area(
                f"Your Answer for Q{i + 1}:",
                value=st.session_state[f"combined_answer_{i}_{label}"],  # Initialize once
                key=f"textarea_{i}_{label}",  # Unique key to avoid conflicts
                height=100
            )

            # Synchronize manual edits back to session state
            if combined_answer != st.session_state[f"combined_answer_{i}_{label}"]:
                st.session_state[f"combined_answer_{i}_{label}"] = combined_answer

            # Handle "Submit Answer" functionality
            if submit_clicked:
                if combined_answer.strip():
                    feedback = evaluate_answer(question, combined_answer, api_key)
                    st.text_area(f"Feedback for Q{i + 1}:", feedback, height=100)

                    # Save progress
                    score = int(feedback.split("Score: ")[-1].split("/")[0]) if "Score:" in feedback else None
                    save_progress(question, combined_answer, feedback, score)
                else:
                    st.warning("Please provide an answer before submitting.")


def main():
    st.title("Job Application Helper with Voice Input")
    st.sidebar.title("Navigation")
    section = st.sidebar.radio("Choose Section", ["Resume Customization", "Interview Preparation", "Custom Interview Prep"])
    api_key = load_config()

    if not api_key:
        st.sidebar.text_input("OpenAI API Key", type="password")

    if not api_key:
        st.warning("Please provide your OpenAI API Key to proceed.")
        return

    if section == "Interview Preparation":
        interview_preparation(api_key)

    if section == "Custom Interview Prep":
        custom_interview_prep(api_key)

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
