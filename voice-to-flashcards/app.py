"""
VoiceToFlashcards AI
---------------------
Speak your lecture. Master your subject.

Main entrypoint: page routing, custom styling, and all UI rendering.
Business logic lives in modules/ and utils/ — this file wires it together.
"""

import streamlit as st
import pandas as pd

from modules.state_manager import init_state, reset_current_pack, save_to_history
from modules.gemini_service import generate_study_pack, GeminiServiceError, DEFAULT_MODEL
from modules.audio_processor import extract_audio, validate_text_notes, AudioValidationError
from modules.flashcard_engine import (
    init_flashcard_progress, mark_known, mark_review, next_card, prev_card, completion_pct,
)
from modules.quiz_engine import grade_quiz
from modules.analytics import (
    history_to_dataframe, quiz_score_trend_fig, difficulty_distribution_fig,
    study_activity_fig, flashcard_progress_fig,
)
from utils.validators import validate_study_pack, SchemaValidationError
from utils.exporters import study_guide_to_markdown, flashcards_to_csv, quiz_to_markdown, full_study_pack_markdown
from utils.helpers import format_timestamp, pct_delta_str, count_delta_str

# --------------------------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="VoiceToFlashcards AI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_state()

# --------------------------------------------------------------------------
# CUSTOM CSS — premium AI/EdTech visual identity
# --------------------------------------------------------------------------
st.markdown(
    """
<style>
    .stApp {
        background: linear-gradient(180deg, #0d1b1e 0%, #142425 100%);
    }
    .v2f-hero {
        background: linear-gradient(135deg, #0f766e 0%, #14b8a6 50%, #fb923c 100%);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(20, 184, 166, 0.25);
    }
    .v2f-hero h1 {
        color: white;
        font-size: 2.2rem;
        margin-bottom: 0.3rem;
    }
    .v2f-hero p {
        color: rgba(255,255,255,0.92);
        font-size: 1.05rem;
        margin: 0;
    }
    .v2f-card {
        background: rgba(20, 184, 166, 0.05);
        border: 1px solid rgba(20, 184, 166, 0.15);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        margin-bottom: 1rem;
    }
    .v2f-feature-card {
        background: rgba(251, 146, 60, 0.05);
        border: 1px solid rgba(251, 146, 60, 0.15);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        height: 100%;
    }
    .v2f-feature-card h3 { margin-bottom: 0.5rem; color: #fdba74; }
    .v2f-flashcard {
        background: linear-gradient(135deg, rgba(20,184,166,0.18), rgba(251,146,60,0.15));
        border: 1px solid rgba(20, 184, 166, 0.35);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        text-align: center;
        min-height: 180px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    .v2f-badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(251, 146, 60, 0.2);
        color: #fdba74;
        margin-right: 0.4rem;
    }
    section[data-testid="stSidebar"] {
        background: #0f1e20;
    }
</style>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# SIDEBAR — NAVIGATION
# --------------------------------------------------------------------------
PAGES = [
    "🏠 Dashboard",
    "🎙️ Record Lecture",
    "📚 Study Guide",
    "🃏 Flashcards",
    "🧠 Quiz",
    "📊 Analytics",
    "🕘 Study History",
    "⚙️ Settings",
]

with st.sidebar:
    st.markdown("## 🎙️ VoiceToFlashcards AI")
    st.caption("Speak your lecture. Master your subject.")
    st.divider()

    chosen = st.radio("Navigate", PAGES, label_visibility="collapsed",
                       index=PAGES.index(st.session_state.page) if st.session_state.page in PAGES else 0)
    st.session_state.page = chosen

    st.divider()
    hist_df = history_to_dataframe(st.session_state.study_history)
    lectures_count = len(hist_df)
    cards_count = int(hist_df["num_flashcards"].sum()) if not hist_df.empty else 0
    avg_score = round(hist_df["quiz_score_pct"].dropna().mean(), 1) if not hist_df.empty and hist_df["quiz_score_pct"].notna().any() else None

    st.markdown("### Session Stats")
    st.metric("Lectures Processed", lectures_count)
    st.metric("Flashcards Created", cards_count)
    st.metric("Average Quiz Score", f"{avg_score}%" if avg_score is not None else "—")

    st.divider()
    st.caption("Built with Streamlit + Gemini")
    st.caption("[GitHub](https://github.com/SarikaDorepally) · [LinkedIn](https://linkedin.com/in/dorepally-sarika-646b92288)")

page = st.session_state.page

# --------------------------------------------------------------------------
# DASHBOARD
# --------------------------------------------------------------------------
if page == "🏠 Dashboard":
    st.markdown(
        """
    <div class="v2f-hero">
        <h1>🎙️ Turn Your Voice Into Knowledge</h1>
        <p>Record a lecture summary and let Gemini transform your thoughts into structured learning material.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button("🎙️ Start Recording", type="primary", use_container_width=False):
        st.session_state.page = "🎙️ Record Lecture"
        st.rerun()

    st.markdown("")
    k1, k2, k3, k4 = st.columns(4)
    quizzes_completed = int(hist_df["quiz_score_pct"].notna().sum()) if not hist_df.empty else 0

    k1.metric("Lectures Processed", lectures_count, delta=count_delta_str(lectures_count, max(lectures_count - 1, 0)) if lectures_count else None)
    k2.metric("Flashcards Created", cards_count, delta=None)
    k3.metric("Quizzes Completed", quizzes_completed, delta=None)
    k4.metric("Average Score", f"{avg_score}%" if avg_score is not None else "—", delta=None)

    st.divider()

    st.markdown("### How it works")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(
            '<div class="v2f-feature-card"><h3>🎤 Speak</h3><p>Record your lecture naturally — no need to organize your thoughts first.</p></div>',
            unsafe_allow_html=True,
        )
    with f2:
        st.markdown(
            '<div class="v2f-feature-card"><h3>🧠 Understand</h3><p>Gemini extracts the important concepts and structures them for you.</p></div>',
            unsafe_allow_html=True,
        )
    with f3:
        st.markdown(
            '<div class="v2f-feature-card"><h3>🃏 Master</h3><p>Practice with AI-generated flashcards and a 5-question quiz.</p></div>',
            unsafe_allow_html=True,
        )

    if not hist_df.empty:
        st.divider()
        st.markdown("### Recent activity")
        recent = hist_df.sort_values("timestamp", ascending=False).head(5)
        st.dataframe(
            recent[["subject", "topic", "difficulty", "num_flashcards", "quiz_score_pct"]],
            use_container_width=True, hide_index=True,
        )

# --------------------------------------------------------------------------
# RECORD LECTURE
# --------------------------------------------------------------------------
elif page == "🎙️ Record Lecture":
    st.markdown("# 🎙️ Record Your Lecture")
    st.markdown(
        "**Speak naturally. Don't worry about grammar, structure, or organization. "
        "VoiceToFlashcards AI will clean everything up.**"
    )

    with st.form("record_form"):
        st.markdown("#### Recording")
        audio_value = st.audio_input("Tap to record your lecture summary")

        with st.expander("Prefer typing? Paste or type your notes instead"):
            text_notes = st.text_area(
                "Typed notes", height=150,
                placeholder="Paste or type your lecture notes here if the mic isn't available...",
            )

        st.markdown("#### Context")
        c1, c2 = st.columns(2)
        with c1:
            subject = st.text_input("Subject", placeholder="e.g. Database Management Systems")
            difficulty = st.selectbox(
                "Difficulty level", ["Beginner", "Intermediate", "Advanced"],
                index=["Beginner", "Intermediate", "Advanced"].index(st.session_state.settings["default_difficulty"]),
            )
        with c2:
            topic_hint = st.text_input("Topic (optional)", placeholder="e.g. Normalization")
            learning_goal = st.selectbox(
                "Learning goal",
                ["Exam preparation", "Quick revision", "Deep understanding", "Interview preparation"],
                index=["Exam preparation", "Quick revision", "Deep understanding", "Interview preparation"].index(
                    st.session_state.settings["default_learning_goal"]
                ),
            )

        submitted = st.form_submit_button("✨ Generate Study Pack", type="primary", use_container_width=True)

    if submitted:
        status = st.empty()
        try:
            status.info("🎧 Processing input...")

            audio_bytes, mime_type, notes = None, None, None
            if audio_value is not None:
                audio_bytes, mime_type = extract_audio(audio_value)
            elif text_notes and text_notes.strip():
                notes = validate_text_notes(text_notes)
            else:
                raise AudioValidationError("Record audio or type your notes before generating.")

            status.info("🧠 Gemini is understanding your lecture...")
            pack = generate_study_pack(
                audio_bytes=audio_bytes,
                audio_mime_type=mime_type,
                text_notes=notes,
                subject=subject.strip(),
                topic_hint=topic_hint.strip(),
                difficulty=difficulty,
                learning_goal=learning_goal,
                num_flashcards=st.session_state.settings["default_num_flashcards"],
                model_name=st.session_state.settings["model"],
            )

            status.info("📚 Building your study guide...")
            pack = validate_study_pack(pack)
            pack["_difficulty"] = difficulty
            pack["_learning_goal"] = learning_goal

            status.info("🃏 Creating flashcards...")
            reset_current_pack()
            st.session_state.current_pack = pack
            st.session_state.study_guide = pack
            st.session_state.flashcards = pack["flashcards"]
            st.session_state.flashcard_progress = init_flashcard_progress(len(pack["flashcards"]))

            status.info("🎯 Preparing your quiz...")
            st.session_state.quiz = pack["quiz"]

            status.empty()
            st.success("Your study pack is ready!")
            st.session_state.page = "📚 Study Guide"
            st.rerun()

        except AudioValidationError as e:
            status.empty()
            st.warning(f"⚠️ {e}")
        except GeminiServiceError as e:
            status.empty()
            st.error(f"⚠️ We couldn't process that recording. {e}")
        except SchemaValidationError as e:
            status.empty()
            st.error(f"⚠️ Gemini's response wasn't structured correctly ({e}). Please try again.")
        except Exception:
            status.empty()
            st.error("⚠️ Something unexpected went wrong. Please try again.")

# --------------------------------------------------------------------------
# STUDY GUIDE
# --------------------------------------------------------------------------
elif page == "📚 Study Guide":
    pack = st.session_state.current_pack
    st.markdown("## 📚 Your AI Study Guide")

    if not pack:
        st.info("No study guide yet — head to **Record Lecture** to generate one.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Topic", pack.get("topic", "—"))
        c2.metric("Difficulty", pack.get("_difficulty", "—"))
        c3.metric("Cards", len(pack.get("flashcards", [])))
        c4.metric("Questions", len(pack.get("quiz", [])))

        st.markdown("### 📝 Quick Summary")
        st.markdown(f'<div class="v2f-card">{pack.get("summary", "")}</div>', unsafe_allow_html=True)

        if pack.get("key_points"):
            st.markdown("### 🔑 Key Points")
            for kp in pack["key_points"]:
                st.markdown(f"- {kp}")

        if pack.get("important_terms"):
            st.markdown("### 📖 Important Terms")
            for term in pack["important_terms"]:
                st.markdown(f"**{term.get('term', '')}** — {term.get('definition', '')}")

        st.markdown("### 💡 Key Concepts")
        for concept in pack.get("study_guide", []):
            with st.expander(f"**{concept.get('concept', 'Concept')}**"):
                st.write(concept.get("explanation", ""))
                if concept.get("why_it_matters"):
                    st.markdown(f"**Why it matters:** {concept['why_it_matters']}")
                if concept.get("example"):
                    st.markdown(f"**Example:** {concept['example']}")

        st.divider()
        st.markdown("### 📥 Export")
        e1, e2, e3, e4 = st.columns(4)
        e1.download_button("📄 Study Guide (.md)", study_guide_to_markdown(pack),
                            file_name="study_guide.md", use_container_width=True)
        e2.download_button("🃏 Flashcards (.csv)", flashcards_to_csv(pack.get("flashcards", [])),
                            file_name="flashcards.csv", use_container_width=True)
        e3.download_button("📝 Quiz (.md)", quiz_to_markdown(pack.get("quiz", [])),
                            file_name="quiz.md", use_container_width=True)
        e4.download_button("📚 Full Pack (.md)", full_study_pack_markdown(pack),
                            file_name="study_pack.md", use_container_width=True)

# --------------------------------------------------------------------------
# FLASHCARDS
# --------------------------------------------------------------------------
elif page == "🃏 Flashcards":
    st.markdown("## 🃏 Flashcards")
    cards = st.session_state.flashcards

    if not cards:
        st.info("No flashcards yet — head to **Record Lecture** to generate some.")
    else:
        progress = st.session_state.flashcard_progress or init_flashcard_progress(len(cards))
        idx = progress["current_index"]
        card = cards[idx]

        st.progress(completion_pct(progress) / 100)
        st.caption(f"Card {idx + 1} of {len(cards)} · {completion_pct(progress)}% reviewed")

        show_answer_key = f"show_answer_{idx}"
        if show_answer_key not in st.session_state:
            st.session_state[show_answer_key] = False

        label = "ANSWER" if st.session_state[show_answer_key] else "QUESTION"
        content = card["answer"] if st.session_state[show_answer_key] else card["question"]
        st.markdown(
            f'<div class="v2f-flashcard"><div><span class="v2f-badge">{label}</span><br><br>{content}</div></div>',
            unsafe_allow_html=True,
        )

        b1, b2, b3, b4, b5 = st.columns(5)
        if b1.button("⬅️ Previous", use_container_width=True, disabled=idx == 0):
            st.session_state.flashcard_progress = prev_card(progress)
            st.rerun()
        if b2.button("👁️ Show Answer", use_container_width=True):
            st.session_state[show_answer_key] = not st.session_state[show_answer_key]
            st.rerun()
        if b3.button("✅ Known", use_container_width=True):
            st.session_state.flashcard_progress = mark_known(progress, idx)
            st.rerun()
        if b4.button("🔁 Review", use_container_width=True):
            st.session_state.flashcard_progress = mark_review(progress, idx)
            st.rerun()
        if b5.button("Next ➡️", use_container_width=True, disabled=idx == len(cards) - 1):
            st.session_state.flashcard_progress = next_card(progress)
            st.rerun()

        st.divider()
        with st.expander("📋 View all flashcards (editable)"):
            cards_df = pd.DataFrame(
                [
                    {
                        "Question": c["question"],
                        "Answer": c["answer"],
                        "Difficulty": c.get("difficulty", "Medium"),
                        "Status": (
                            "Known" if i in progress["known"]
                            else "Review" if i in progress["review"]
                            else "Unseen"
                        ),
                    }
                    for i, c in enumerate(cards)
                ]
            )
            st.data_editor(
                cards_df,
                column_config={
                    "Difficulty": st.column_config.SelectboxColumn(options=["Easy", "Medium", "Hard"]),
                    "Status": st.column_config.SelectboxColumn(options=["Known", "Review", "Unseen"]),
                },
                hide_index=True, use_container_width=True, key="all_cards_editor",
            )

# --------------------------------------------------------------------------
# QUIZ
# --------------------------------------------------------------------------
elif page == "🧠 Quiz":
    st.markdown("## 🧠 Quiz")
    quiz = st.session_state.quiz

    if not quiz:
        st.info("No quiz yet — head to **Record Lecture** to generate one.")
    elif st.session_state.quiz_result:
        result = st.session_state.quiz_result
        st.markdown("# 🎯 Quiz Complete!")
        m1, m2 = st.columns(2)
        m1.metric("Score", f"{result['correct_count']} / {result['total']}")
        m2.metric("Percentage", f"{result['score_pct']}%")
        st.info(result["message"])

        for r in result["results"]:
            if r["is_correct"]:
                st.success(f"Q: {r['question']}\n\nYour answer: {r['selected']} ✅")
            else:
                st.error(
                    f"Q: {r['question']}\n\nYour answer: {r['selected']} ❌ · "
                    f"Correct: {r['correct_answer']}\n\n{r['explanation']}"
                )

        if st.button("🔁 Retake Quiz"):
            st.session_state.quiz_answers = {}
            st.session_state.quiz_result = None
            st.rerun()

        if st.button("💾 Save to Study History", type="primary"):
            save_to_history(st.session_state.current_pack, result)
            st.success("Saved to your study history.")
    else:
        with st.form("quiz_form"):
            for i, q in enumerate(quiz):
                st.markdown(f"### Question {i + 1} / {len(quiz)}")
                st.markdown(f"**{q['question']}**")
                choice = st.radio(
                    f"q_{i}", options=q["options"], key=f"quiz_choice_{i}",
                    label_visibility="collapsed",
                )
                st.session_state.quiz_answers[i] = choice
                st.markdown("")

            quiz_submitted = st.form_submit_button("Submit Answer", type="primary", use_container_width=True)

        if quiz_submitted:
            st.session_state.quiz_result = grade_quiz(quiz, st.session_state.quiz_answers)
            st.rerun()

# --------------------------------------------------------------------------
# ANALYTICS
# --------------------------------------------------------------------------
elif page == "📊 Analytics":
    st.markdown("## 📊 Performance Analytics")

    if hist_df.empty:
        st.info("No study history yet — complete a lecture and quiz to see analytics here.")
    else:
        trend_fig = quiz_score_trend_fig(hist_df)
        diff_fig = difficulty_distribution_fig(hist_df)
        activity_fig = study_activity_fig(hist_df)

        c1, c2 = st.columns(2)
        with c1:
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True)
            else:
                st.caption("No quiz attempts yet to chart.")
        with c2:
            if diff_fig:
                st.plotly_chart(diff_fig, use_container_width=True)

        if activity_fig:
            st.plotly_chart(activity_fig, use_container_width=True)

        progress = st.session_state.flashcard_progress
        if progress:
            fc_fig = flashcard_progress_fig(
                known=len(progress["known"]),
                review=len(progress["review"]),
                unseen=progress["total"] - len(progress["known"]) - len(progress["review"]),
            )
            if fc_fig:
                st.plotly_chart(fc_fig, use_container_width=True)

# --------------------------------------------------------------------------
# STUDY HISTORY
# --------------------------------------------------------------------------
elif page == "🕘 Study History":
    st.markdown("## 🕘 Study History")

    if hist_df.empty:
        st.info("No sessions saved yet. Complete a quiz and save it from the Quiz page.")
    else:
        display_df = hist_df.copy()
        display_df["timestamp"] = display_df["timestamp"].apply(lambda t: format_timestamp(t.isoformat()) if pd.notna(t) else "—")
        edited = st.data_editor(
            display_df[["timestamp", "subject", "topic", "difficulty", "num_flashcards", "quiz_score_pct"]],
            hide_index=True, use_container_width=True, key="history_editor",
        )

        st.divider()
        options = [f"{h['subject']} — {h['topic']} ({format_timestamp(h['timestamp'])})" for h in st.session_state.study_history]
        selected = st.selectbox("Reload a previous session", ["—"] + options)
        if selected != "—":
            idx = options.index(selected)
            entry = st.session_state.study_history[idx]
            if st.button("📂 Load this session"):
                pack = entry["pack_snapshot"]
                reset_current_pack()
                st.session_state.current_pack = pack
                st.session_state.study_guide = pack
                st.session_state.flashcards = pack["flashcards"]
                st.session_state.flashcard_progress = init_flashcard_progress(len(pack["flashcards"]))
                st.session_state.quiz = pack["quiz"]
                st.session_state.page = "📚 Study Guide"
                st.rerun()

# --------------------------------------------------------------------------
# SETTINGS
# --------------------------------------------------------------------------
elif page == "⚙️ Settings":
    st.markdown("## ⚙️ Settings")

    with st.form("settings_form"):
        model_options = ["gemini-3.6-flash"]
        model = st.selectbox(
            "Gemini model", model_options,
            index=model_options.index(st.session_state.settings["model"])
            if st.session_state.settings["model"] in model_options else 0,
        )
        st.caption(
            "Only gemini-3.6-flash is listed here since that's the model confirmed "
            "working via the API error message. If Google adds other current model "
            "names later, add them to this list."
        )
        default_difficulty = st.selectbox(
            "Default difficulty", ["Beginner", "Intermediate", "Advanced"],
            index=["Beginner", "Intermediate", "Advanced"].index(st.session_state.settings["default_difficulty"]),
        )
        default_num_flashcards = st.slider("Default number of flashcards", min_value=5, max_value=15,
                                            value=st.session_state.settings["default_num_flashcards"])
        default_learning_goal = st.selectbox(
            "Default learning goal",
            ["Exam preparation", "Quick revision", "Deep understanding", "Interview preparation"],
            index=["Exam preparation", "Quick revision", "Deep understanding", "Interview preparation"].index(
                st.session_state.settings["default_learning_goal"]
            ),
        )

        saved = st.form_submit_button("Save Settings", type="primary")

    if saved:
        st.session_state.settings = {
            "model": model,
            "default_difficulty": default_difficulty,
            "default_num_flashcards": default_num_flashcards,
            "default_learning_goal": default_learning_goal,
        }
        st.success("Settings saved.")

    st.divider()
    st.caption("Your Gemini API key is read from `st.secrets['GEMINI_API_KEY']` and is never shown or stored here.")
