import speech_recognition as sr

def record_audio_segment():
    """Record a segment of audio and convert it to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source, timeout=10)  # Listen for 10 seconds
            text = recognizer.recognize_google(audio)  # Convert to text
            return text
        except sr.UnknownValueError:
            return "Could not understand audio."
        except sr.RequestError as e:
            return f"Error with the recognition service: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"
