"""
Exporters
---------
Builds the text/CSV/Markdown payloads used by st.download_button.
No file-system writes — everything is returned as an in-memory string
so it works on Streamlit Community Cloud's read-only filesystem.
"""

import io
import csv


def study_guide_to_markdown(pack: dict) -> str:
    lines = [
        f"# {pack.get('topic', 'Study Guide')}",
        f"**Subject:** {pack.get('subject', '—')}",
        "",
        "## Summary",
        pack.get("summary", ""),
        "",
        "## Key Points",
    ]
    for kp in pack.get("key_points", []):
        lines.append(f"- {kp}")

    lines.append("\n## Important Terms")
    for term in pack.get("important_terms", []):
        lines.append(f"- **{term.get('term', '')}**: {term.get('definition', '')}")

    lines.append("\n## Study Guide")
    for concept in pack.get("study_guide", []):
        lines.append(f"\n### {concept.get('concept', '')}")
        lines.append(concept.get("explanation", ""))
        if concept.get("why_it_matters"):
            lines.append(f"\n*Why it matters:* {concept['why_it_matters']}")
        if concept.get("example"):
            lines.append(f"\n*Example:* {concept['example']}")

    return "\n".join(lines)


def flashcards_to_csv(flashcards: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Question", "Answer", "Difficulty", "Topic"])
    for c in flashcards:
        writer.writerow([c.get("question", ""), c.get("answer", ""), c.get("difficulty", ""), c.get("topic", "")])
    return output.getvalue()


def quiz_to_markdown(quiz: list[dict]) -> str:
    lines = ["# Quiz\n"]
    for i, q in enumerate(quiz, start=1):
        lines.append(f"**{i}. {q.get('question', '')}**")
        for opt in q.get("options", []):
            marker = "✅" if opt == q.get("correct_answer") else "◻️"
            lines.append(f"- {marker} {opt}")
        if q.get("explanation"):
            lines.append(f"\n*Explanation:* {q['explanation']}")
        lines.append("")
    return "\n".join(lines)


def full_study_pack_markdown(pack: dict) -> str:
    parts = [
        study_guide_to_markdown(pack),
        "\n---\n\n# Flashcards\n",
    ]
    for c in pack.get("flashcards", []):
        parts.append(f"**Q:** {c.get('question', '')}  \n**A:** {c.get('answer', '')}\n")
    parts.append("\n---\n")
    parts.append(quiz_to_markdown(pack.get("quiz", [])))
    return "\n".join(parts)
