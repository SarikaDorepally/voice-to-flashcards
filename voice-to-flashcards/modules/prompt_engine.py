"""
Prompt Engineering Layer
-------------------------
Defines VoiceToFlashcards AI's system instruction and builds dynamic,
context-aware prompts. This module is what stops the app from being
"just a chatbot" — Gemini is given a fixed role, strict output schema,
and per-request context injected via f-strings.
"""

SYSTEM_INSTRUCTION = """You are VoiceToFlashcards AI, an expert educational
content transformation engine. Your sole purpose is to transform unstructured,
spoken student lecture audio (or informal typed notes) into accurate,
structured, exam-friendly learning material.

You are NOT a general-purpose chatbot. You do not chat, ask follow-up
questions, or add conversational filler. You receive raw input and return
a single structured JSON object.

Your responsibilities, in order:
1. Transcribe the input accurately. Preserve technical terminology exactly
   as spoken — do not "simplify" domain-specific terms.
2. Clean obvious filler words (um, like, so basically) without changing
   the meaning of what the student said.
3. Identify the subject and topic, even if the student never states them
   explicitly.
4. Extract only high-value concepts — do not pad the output with trivial
   restatements.
5. Generate a structured study guide from what was actually said.
6. Generate flashcards strictly from the transcript content.
7. Generate exactly 5 multiple-choice quiz questions strictly from the
   transcript content.

Hard constraints:
- NEVER invent facts, dates, numbers, or claims that are not present or
  reasonably inferable from the transcript. If the lecture content is too
  thin to support a confident concept, say so in the summary rather than
  fabricating detail.
- If part of the audio is unclear or ambiguous, mark it as uncertain in
  the transcript rather than guessing definitively.
- Match difficulty and depth to the requested difficulty level.
- Keep explanations student-friendly and concrete — use a short example
  wherever a concept benefits from one.
- Every flashcard and quiz question must be traceable back to something
  actually said in the lecture — no generic textbook filler unrelated to
  the specific recording.

Return ONLY valid JSON. No markdown fences, no preamble, no commentary
outside the JSON object.
"""

OUTPUT_SCHEMA = """{
  "topic": "string - the specific topic covered",
  "subject": "string - the broader subject area",
  "summary": "string - 3-5 sentence clean summary",
  "key_points": ["string", "..."],
  "important_terms": [
    {"term": "string", "definition": "string"}
  ],
  "study_guide": [
    {
      "concept": "string",
      "explanation": "string",
      "why_it_matters": "string",
      "example": "string"
    }
  ],
  "flashcards": [
    {
      "question": "string",
      "answer": "string",
      "difficulty": "Easy | Medium | Hard",
      "topic": "string"
    }
  ],
  "quiz": [
    {
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "correct_answer": "string - must exactly match one of the options",
      "explanation": "string",
      "difficulty": "Easy | Medium | Hard"
    }
  ]
}"""


def build_prompt(
    subject: str,
    topic_hint: str,
    difficulty: str,
    learning_goal: str,
    num_flashcards: int = 8,
) -> str:
    """
    Builds the dynamic portion of the prompt using f-strings to inject
    per-request context. This is what makes the AI behave as a tailored
    engine rather than a static, one-size-fits-all prompt.
    """
    subject_line = (
        f"The student has tagged this as: {subject}."
        if subject
        else "The student did not specify a subject — infer it from the content."
    )
    topic_line = (
        f"They've hinted the topic is: {topic_hint}."
        if topic_hint
        else ""
    )

    difficulty_guidance = {
        "Beginner": "Use simple language, avoid jargon unless defined, "
                    "favor intuitive examples over formal definitions.",
        "Intermediate": "Assume basic familiarity with the subject. Use "
                         "standard terminology, but still explain non-obvious "
                         "concepts.",
        "Advanced": "Assume strong prior knowledge. Use precise technical "
                    "terminology, focus on nuance, edge cases, and deeper "
                    "reasoning rather than basic definitions.",
    }.get(difficulty, "Use standard terminology appropriate for a college student.")

    goal_guidance = {
        "Exam preparation": "Prioritize the concepts most likely to appear "
                             "in an exam. Quiz questions should mimic exam-style "
                             "phrasing.",
        "Quick revision": "Keep the study guide tight and skimmable. "
                           "Prioritize breadth over depth.",
        "Deep understanding": "Prioritize the 'why' behind each concept. "
                               "Favor explanations that build intuition over "
                               "quick facts.",
        "Interview preparation": "Frame explanations the way you would "
                                  "answer a technical interview question — "
                                  "concise, precise, and example-backed.",
    }.get(learning_goal, "Balance breadth and depth appropriately.")

    prompt = f"""{subject_line}
{topic_line}

Difficulty level: {difficulty}
{difficulty_guidance}

Learning goal: {learning_goal}
{goal_guidance}

Generate exactly {num_flashcards} flashcards and exactly 5 quiz questions.
Each quiz question must have exactly 4 options with exactly one correct answer.

Return your response as a single JSON object matching exactly this schema:

{OUTPUT_SCHEMA}
"""
    return prompt
