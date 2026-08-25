"""
Audio Processor
---------------
Validates and extracts bytes/mime type from a Streamlit st.audio_input
UploadedFile-like object. Keeps validation logic out of app.py.
"""


class AudioValidationError(Exception):
    pass


MIN_AUDIO_BYTES = 500  # guards against empty/near-empty recordings


def extract_audio(audio_value) -> tuple[bytes, str]:
    """Given the object returned by st.audio_input, return (bytes, mime_type).
    Raises AudioValidationError if the recording looks empty or invalid."""
    if audio_value is None:
        raise AudioValidationError("No recording was captured.")

    try:
        audio_bytes = audio_value.getvalue()
    except Exception:
        raise AudioValidationError("Couldn't read the recording. Please try again.")

    if not audio_bytes or len(audio_bytes) < MIN_AUDIO_BYTES:
        raise AudioValidationError(
            "That recording looks empty or too short. Please record at least "
            "a few seconds of audio."
        )

    mime_type = getattr(audio_value, "type", None) or "audio/wav"
    return audio_bytes, mime_type


def validate_text_notes(text: str) -> str:
    """Validates typed-note fallback input."""
    cleaned = (text or "").strip()
    if len(cleaned) < 20:
        raise AudioValidationError(
            "Typed notes look too short to generate meaningful study material. "
            "Add a bit more detail."
        )
    return cleaned
