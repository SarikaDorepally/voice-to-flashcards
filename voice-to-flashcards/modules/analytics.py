"""
Analytics
---------
Turns raw study_history (a list of dicts in session_state) into tidy
Pandas DataFrames and Plotly figures. This is the app's data pipeline:
session state -> DataFrame -> chart.
"""

import pandas as pd
import plotly.express as px


def history_to_dataframe(history: list[dict]) -> pd.DataFrame:
    if not history:
        return pd.DataFrame(
            columns=[
                "timestamp", "subject", "topic", "difficulty",
                "learning_goal", "num_flashcards", "num_quiz_questions",
                "quiz_score_pct",
            ]
        )
    df = pd.DataFrame(
        [
            {
                "timestamp": h["timestamp"],
                "subject": h["subject"],
                "topic": h["topic"],
                "difficulty": h["difficulty"],
                "learning_goal": h["learning_goal"],
                "num_flashcards": h["num_flashcards"],
                "num_quiz_questions": h["num_quiz_questions"],
                "quiz_score_pct": h["quiz_score_pct"],
            }
            for h in history
        ]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df.sort_values("timestamp").reset_index(drop=True)


def quiz_score_trend_fig(df: pd.DataFrame):
    scored = df.dropna(subset=["quiz_score_pct"])
    if scored.empty:
        return None
    scored = scored.copy()
    scored["attempt"] = range(1, len(scored) + 1)
    fig = px.line(
        scored, x="attempt", y="quiz_score_pct", markers=True,
        title="Quiz Performance Over Attempts",
        labels={"attempt": "Attempt #", "quiz_score_pct": "Score (%)"},
    )
    fig.update_layout(yaxis_range=[0, 100])
    return fig


def difficulty_distribution_fig(df: pd.DataFrame):
    if df.empty:
        return None
    counts = df["difficulty"].value_counts().reset_index()
    counts.columns = ["difficulty", "count"]
    fig = px.bar(
        counts, x="difficulty", y="count",
        title="Lectures by Difficulty Level",
        labels={"difficulty": "Difficulty", "count": "Lectures"},
        color="difficulty",
    )
    return fig


def study_activity_fig(df: pd.DataFrame):
    if df.empty:
        return None
    daily = df.copy()
    daily["date"] = daily["timestamp"].dt.date
    daily_counts = daily.groupby("date").size().reset_index(name="lectures")
    fig = px.bar(
        daily_counts, x="date", y="lectures",
        title="Study Activity by Date",
        labels={"date": "Date", "lectures": "Lectures Processed"},
    )
    return fig


def flashcard_progress_fig(known: int, review: int, unseen: int):
    if known + review + unseen == 0:
        return None
    fig = px.pie(
        names=["Known", "Reviewing", "Unseen"],
        values=[known, review, unseen],
        title="Flashcard Progress (Current Deck)",
        color_discrete_sequence=["#22c55e", "#f59e0b", "#94a3b8"],
    )
    return fig
