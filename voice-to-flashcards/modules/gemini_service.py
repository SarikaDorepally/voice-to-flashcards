"""
Gemini Service
--------------
Thin wrapper around the Gemini API. Handles key resolution, the actual
multimodal call (audio OR text), and JSON parsing/cleanup. Keeps all
Gemini-specific plumbing out of app.py and out of the UI layer.
"""

import json
import os

import google.generativeai as genai

from modules.prompt_engine import SYSTEM_INSTRUCTION, build_prompt

DEFAULT_MODEL = "gemini-3.6-flash"


class GeminiServiceError(Exception):
    """Raised for any recoverable Gemini/service failure — the UI layer
    catches this and shows a friendly message instead of a stack trace."""
    pass


def get_api_key() -> str:
    """Resolve the Gemini API key from Streamlit secrets first, then env var.
    Returns an empty string if neither is configured."""
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY", "")


def _configure():
    key = get_api_key()
    if not key:
        raise GeminiServiceError(
            "No Gemini API key found. Add GEMINI_API_KEY to .streamlit/secrets.toml "
            "or your environment."
        )
    genai.configure(api_key=key)
    return key


def _clean_json_text(raw_text: str) -> str:
    """Defensive cleanup in case the model wraps output in code fences
    despite the JSON-mode instruction."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json\n"):
            text = text[5:]
    return text.strip()


def generate_study_pack(
    *,
    audio_bytes: bytes | None,
    audio_mime_type: str | None,
    text_notes: str | None,
    subject: str,
    topic_hint: str,
    difficulty: str,
    learning_goal: str,
    num_flashcards: int,
    model_name: str = DEFAULT_MODEL,
) -> dict:
    """
    Calls Gemini with either audio or typed notes (exactly one must be
    provided) and returns the parsed structured study pack.

    Raises GeminiServiceError on any failure — the caller (app.py) is
    responsible for turning that into a friendly UI message.
    """
    if not audio_bytes and not text_notes:
        raise GeminiServiceError("No audio or text input was provided.")

    _configure()

    dynamic_prompt = build_prompt(
        subject=subject,
        topic_hint=topic_hint,
        difficulty=difficulty,
        learning_goal=learning_goal,
        num_flashcards=num_flashcards,
    )

    full_prompt = f"{SYSTEM_INSTRUCTION}\n\n{dynamic_prompt}"

    try:
        model = genai.GenerativeModel(model_name)

        content_parts = [full_prompt]
        if audio_bytes:
            content_parts.append({"mime_type": audio_mime_type or "audio/wav", "data": audio_bytes})
        else:
            content_parts.append(f"\nRaw lecture notes (typed, not audio):\n{text_notes}")

        response = model.generate_content(
            content_parts,
            generation_config={"response_mime_type": "application/json"},
        )

        if not response or not getattr(response, "text", None):
            raise GeminiServiceError("Gemini returned an empty response.")

        cleaned = _clean_json_text(response.text)
        parsed = json.loads(cleaned)
        return parsed

    except json.JSONDecodeError:
        raise GeminiServiceError(
            "Gemini's response couldn't be parsed as structured data. "
            "Try again, or shorten the recording."
        )
    except GeminiServiceError:
        raise
    except Exception as e:
        raise GeminiServiceError(f"Gemini request failed: {e}")
