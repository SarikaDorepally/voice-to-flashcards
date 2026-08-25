"""
State Manager
-------------
Single place that defines and initializes every st.session_state key
the app uses. Prevents scattered, inconsistent defaults across pages
and makes the full state shape easy to audit.
"""

import streamlit as st

DEFAULTS = {
    "page": "Dashboard",
    "audio_bytes": None,
    "audio_mime_type": None,
    "transcript": None,
    "study_guide": None,
    "flashcards": None,
    "quiz": None,
    "quiz_answers": {},
    "quiz_result": None,
    "flashcard_progress": None,
    "study_history": [],          # list of completed-lecture summary dicts
    "processing_status": None,
    "selected_session": None,
    "current_pack": None,         # the full generated study pack (topic, subject, etc.)
    "settings": {
        "model": "gemini-3.6-flash",
        "default_difficulty": "Intermediate",
        "default_num_flashcards": 8,
        "default_learning_goal": "Exam preparation",
    },
}


def init_state():
    for key, val in DEFAULTS.items():
        if key not in st.session_state:
            # use a fresh copy for mutable defaults
            st.session_state[key] = val.copy() if isinstance(val, (dict, list)) else val


def reset_current_pack():
    """Clears the current study pack / flashcards / quiz without touching
    study_history — used when starting a new recording."""
    st.session_state.transcript = None
    st.session_state.study_guide = None
    st.session_state.flashcards = None
    st.session_state.quiz = None
    st.session_state.quiz_answers = {}
    st.session_state.quiz_result = None
    st.session_state.flashcard_progress = None
    st.session_state.current_pack = None


def save_to_history(pack: dict, quiz_result: dict | None):
    """Appends a completed session summary to study_history."""
    from datetime import datetime

    entry = {
        "timestamp": datetime.now().isoformat(),
        "subject": pack.get("subject", "Untitled"),
        "topic": pack.get("topic", "Untitled"),
        "difficulty": pack.get("_difficulty", "Intermediate"),
        "learning_goal": pack.get("_learning_goal", "Exam preparation"),
        "num_flashcards": len(pack.get("flashcards", [])),
        "num_quiz_questions": len(pack.get("quiz", [])),
        "quiz_score_pct": quiz_result["score_pct"] if quiz_result else None,
        "pack_snapshot": pack,
    }
    st.session_state.study_history.append(entry)
