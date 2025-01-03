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

    if "custom_questions" not in st.session_state:
        st.session_state.custom_questions = [{
            "question": "",
            "answer": "",
            "feedback": "",
        }]

    for idx, q_data in enumerate(st.session_state.custom_questions):
        st.subheader(f"Question {idx + 1}")
        question = st.text_area(
            "Enter or Edit Question:",
            value=q_data["question"],
            key=f"custom_question_{idx}",
            height=100
        )
        st.session_state.custom_questions[idx]["question"] = question

        cols = st.columns(2)
        with cols[0]:
            record_clicked = st.button(f"Record Answer for Q{idx + 1}", key=f"record_{idx}")
        with cols[1]:
            submit_clicked = st.button(f"Submit Answer for Q{idx + 1}", key=f"submit_{idx}")

        if record_clicked:
            recorded_text = record_audio()
            st.session_state.custom_questions[idx]["answer"] += f" {recorded_text}".strip()

        answer = st.text_area(
            f"Your Answer for Q{idx + 1}:",
            value=st.session_state.custom_questions[idx]["answer"],
            key=f"answer_{idx}",
            height=100
        )
        st.session_state.custom_questions[idx]["answer"] = answer

        if submit_clicked:
            if answer.strip():
                with st.spinner("Evaluating your answer, please wait..."):
                    feedback = evaluate_answer(question, answer, api_key)
                st.session_state.custom_questions[idx]["feedback"] = feedback
                st.text_area(f"Feedback for Q{idx + 1}:", feedback, height=100)

                save_progress(question, answer, feedback, score=None)
            else:
                st.warning("Please provide an answer before submitting.")

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
        with st.spinner("Generating mock questions, please wait..."):
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

    for question_set, label in zip(
            [st.session_state.get("behavioral_questions", []), st.session_state.get("technical_questions", [])],
            ["Behavioral", "Technical"]
    ):
        for i, question in enumerate(question_set):
            st.write(f"Q{i + 1}: {question}")

            cols = st.columns(2)
            with cols[0]:
                record_clicked = st.button(f"Record Answer for Q{i + 1}", key=f"record_{i}_{label}")
            with cols[1]:
                submit_clicked = st.button(f"Submit Answer for Q{i + 1}", key=f"submit_{i}_{label}")

            if f"combined_answer_{i}_{label}" not in st.session_state:
                st.session_state[f"combined_answer_{i}_{label}"] = ""

            if record_clicked:
                recorded_text = record_audio()
                st.session_state[f"combined_answer_{i}_{label}"] += f" {recorded_text}".strip()

            combined_answer = st.text_area(
                f"Your Answer for Q{i + 1}:",
                value=st.session_state[f"combined_answer_{i}_{label}"],
                key=f"textarea_{i}_{label}",
                height=100
            )

            if combined_answer != st.session_state[f"combined_answer_{i}_{label}"]:
                st.session_state[f"combined_answer_{i}_{label}"] = combined_answer

            if submit_clicked:
                if combined_answer.strip():
                    with st.spinner("Evaluating your answer, please wait..."):
                        feedback = evaluate_answer(question, combined_answer, api_key)
                        st.session_state[f"feedback_{i}_{label}"] = feedback

                    st.text_area(f"Feedback for Q{i + 1}:", st.session_state[f"feedback_{i}_{label}"], height=100)

                    score = float(feedback.split("Score: ")[-1].split("/")[0]) if "Score:" in feedback else None
                    save_progress(question, combined_answer, st.session_state[f"feedback_{i}_{label}"], score)
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

    if "resume_content" not in st.session_state:
        st.session_state.resume_content = ""
    if "job_description" not in st.session_state:
        st.session_state.job_description = ""
    if "custom_questions" not in st.session_state:
        st.session_state.custom_questions = [{
            "question": "",
            "answer": "",
            "feedback": "",
        }]
    if "behavioral_questions" not in st.session_state:
        st.session_state.behavioral_questions = []
    if "technical_questions" not in st.session_state:
        st.session_state.technical_questions = []

    if section == "Resume Customization":
        st.header("Resume Customization")

        job_description = st.text_area("Enter Job Description:", height=150, value=st.session_state.job_description)
        st.session_state.job_description = job_description

        uploaded_file = st.file_uploader("Upload Resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
        if uploaded_file:
            resume_content = extract_text_from_file(uploaded_file)
            st.session_state.resume_content = resume_content

        st.text_area("Uploaded Resume Content:", st.session_state.resume_content, height=150)

        if st.button("Customize Resume"):
            customized_resume = customize_resume(job_description, st.session_state.resume_content, api_key)
            st.text_area("Customized Resume:", customized_resume, height=300)

    elif section == "Interview Preparation":
        interview_preparation(api_key)

    elif section == "Custom Interview Prep":
        custom_interview_prep(api_key)

if __name__ == "__main__":
    create_database()
    main()