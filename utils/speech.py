# import speech_recognition as sr
from typing import Optional

def record_and_transcribe(
    timeout: int = 5,
    phrase_time_limit: int = 10,
    verbose: bool = True
) -> Optional[str]:
    return None
    """
    Capture audio from microphone and transcribe it using Google Speech API.

    Args:
        timeout (int): Seconds to wait for speech to start.
        phrase_time_limit (int): Max duration to listen for.
        verbose (bool): If True, print messages. Set to False in UI mode.

    Returns:
        Optional[str]: Transcribed text, or None if failed.
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        if verbose:
            print("🎤 Listening... Please speak.")
        recognizer.adjust_for_ambient_noise(source, duration=1)

        try:
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit
            )
            if verbose:
                print("🧠 Transcribing...")
            text = recognizer.recognize_google(audio)
            if verbose:
                print("✅ You said:", text)
            return text

        except sr.WaitTimeoutError:
            if verbose:
                print("⏱️ Timeout: No speech detected.")
        except sr.UnknownValueError:
            if verbose:
                print("❌ Could not understand audio.")
        except sr.RequestError as e:
            if verbose:
                print("🌐 API Error:", e)

    return None