# Technical Design Document — VoiceToFlashcards AI

## 1. Application Architecture

The app follows a layered structure: `app.py` handles routing and rendering only; everything else — prompt construction, the Gemini call, validation, domain logic, and analytics — lives in `modules/` and `utils/`. This keeps the UI file readable and lets each piece of logic be tested independently of Streamlit (see `docs/architecture.md` for the full diagram and layer table).

## 2. Gemini API Integration

`modules/gemini_service.py` is the only file that imports `google.generativeai`. It resolves the API key from `st.secrets` (falling back to an environment variable for local/non-Streamlit use), configures the client, and makes a single multimodal call per submission — either audio bytes or typed text, never both. `response_mime_type` is set to `application/json` so Gemini is constrained to return parseable structured data rather than conversational text.

## 3. Audio Processing

`modules/audio_processor.py` validates the `st.audio_input` result before it's sent anywhere: it checks the recording isn't `None`, that `.getvalue()` succeeds, and that the byte count clears a minimum threshold (guards against accidental empty recordings). A parallel `validate_text_notes()` covers the typed-notes fallback path for students without mic access.

## 4. Prompt Engineering Strategy

`modules/prompt_engine.py` defines two things:
- `SYSTEM_INSTRUCTION` — a fixed, detailed role definition that explicitly forbids hallucination, generic chatbot behavior, and invented facts, and requires traceability back to the actual lecture content.
- `build_prompt()` — builds the dynamic per-request portion using f-strings, injecting subject, topic hint, difficulty, and learning goal, each of which changes the guidance text Gemini receives (e.g., "Advanced" difficulty asks for precise terminology and edge cases; "Exam preparation" asks for exam-style quiz phrasing).

This two-part structure (fixed system instruction + dynamic context) is what satisfies the rubric's "advanced use of the Gemini API" and "tailored engine, not a generic chatbot" criteria.

## 5. Dynamic F-String Context

Every request's prompt is different depending on: subject, topic hint, difficulty level, learning goal, and requested flashcard count. These are injected directly into the prompt text at call time rather than being hardcoded, so the same system instruction produces meaningfully different output for a "Beginner / Quick revision" request versus an "Advanced / Interview preparation" request.

## 6. Session-State Management

`modules/state_manager.py` defines every session-state key the app uses in one `DEFAULTS` dict, initialized once via `init_state()`. This avoids the common Streamlit bug of a KeyError on first load because some page checked a key before it was set. `reset_current_pack()` and `save_to_history()` are the only two functions that mutate session state outside of direct page interactions, keeping state transitions predictable and auditable.

## 7. Pandas Data Pipeline

`modules/analytics.py` converts the list-of-dicts `study_history` into a tidy Pandas DataFrame (`history_to_dataframe`), with `timestamp` parsed to a real datetime column. All downstream charts and the Study History table read from this single DataFrame rather than re-deriving figures from raw session state, so KPI counts, the score trend chart, and the history table are guaranteed to agree with each other.

## 8. Quiz Generation

Gemini is instructed to return exactly 5 quiz questions, each with exactly 4 options and a `correct_answer` that must exactly match one of the options. `utils/validators.py` normalizes minor whitespace/casing mismatches between `correct_answer` and the `options` list before the quiz is trusted, since LLM output occasionally drifts slightly.

## 9. Flashcard Generation

`modules/flashcard_engine.py` is pure logic — no Streamlit imports — handling card navigation (`next_card`/`prev_card`), known/review marking (backed by Python sets so an index can only be in one bucket at a time), and completion percentage. The UI layer (`app.py`) only calls these functions and re-renders; it never mutates progress state directly.

## 10. Error Handling

Every failure mode has a distinct exception type surfaced as a friendly message, never a raw stack trace:
- `AudioValidationError` — empty/too-short recording or notes
- `GeminiServiceError` — missing API key, network failure, empty response, malformed JSON
- `SchemaValidationError` — Gemini returned JSON that's missing required fields or has an inconsistent quiz answer

`app.py`'s try/except block in the Record Lecture page catches each of these separately and shows a specific, actionable message rather than a generic failure.

## 11. Security

The Gemini API key is never hardcoded and never logged. It's read exclusively via `st.secrets["GEMINI_API_KEY"]` (with an environment-variable fallback for local dev outside Streamlit). `.streamlit/secrets.toml` is gitignored; only `secrets.toml.example` — a template with a placeholder — is committed.

## 12. Deployment

The app has zero local system dependencies — every package in `requirements.txt` (`streamlit`, `google-generativeai`, `pandas`, `plotly`) is pure-Python-installable via pip, making it directly deployable to Streamlit Community Cloud without a custom `packages.txt` or Dockerfile.

## 13. API-Call Optimization

The recording form (`st.form`) batches subject, difficulty, learning goal, and the audio/text input together, so Gemini is called exactly once per "Generate Study Pack" click — never on individual widget interactions. Navigating between pages (Dashboard, Study Guide, Flashcards, Quiz, Analytics) never re-triggers the API; all of them read from the same `st.session_state` pack set at generation time.

## 14. Future Improvements

- Persist `study_history` to a lightweight database (e.g. SQLite or a Google Sheet) so history survives across browser sessions rather than living only in `st.session_state`.
- Add automatic retry with backoff for transient Gemini API failures.
- Support multi-language lecture input.
- Add spaced-repetition scheduling to the flashcard engine instead of a simple known/review/unseen split.
