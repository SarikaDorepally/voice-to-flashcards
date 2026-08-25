"""
Quiz Engine
-----------
Pure scoring logic for the 5-question quiz. Separated from rendering
so the grading logic is easy to reason about and reuse (e.g. from the
analytics module when rebuilding history).
"""


def grade_quiz(quiz: list[dict], answers: dict[int, str]) -> dict:
    """
    quiz: list of {"question", "options", "correct_answer", "explanation", ...}
    answers: {question_index: selected_option_string}

    Returns a result dict with per-question correctness and an overall score.
    """
    results = []
    correct_count = 0

    for i, q in enumerate(quiz):
        selected = answers.get(i)
        is_correct = selected == q.get("correct_answer")
        if is_correct:
            correct_count += 1
        results.append(
            {
                "index": i,
                "question": q.get("question", ""),
                "selected": selected,
                "correct_answer": q.get("correct_answer", ""),
                "is_correct": is_correct,
                "explanation": q.get("explanation", ""),
            }
        )

    total = len(quiz)
    pct = round(100 * correct_count / total, 1) if total else 0.0

    if pct >= 90:
        message = "Outstanding — you've clearly got this down."
    elif pct >= 70:
        message = "Solid work — a quick review of the misses and you're set."
    elif pct >= 50:
        message = "Decent start — worth revisiting the concepts you missed."
    else:
        message = "This topic needs another pass — review the study guide and retry."

    return {
        "results": results,
        "correct_count": correct_count,
        "total": total,
        "score_pct": pct,
        "message": message,
    }
