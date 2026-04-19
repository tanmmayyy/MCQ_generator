# ─────────────────────────────────────────────
#  app/components.py
#  Reusable Streamlit UI building blocks.
#  Keeps main.py clean and focused on flow logic.
# ─────────────────────────────────────────────

import streamlit as st
from src.mcq_builder import MCQ


def render_question_card(mcq: MCQ, index: int) -> str | None:
    """
    Render a question with labelled radio button options.
    Returns the selected option label ("A"/"B"/"C"/"D") or None.
    """
    st.markdown(f"### Q{index + 1}. {mcq.question}")

    # Build labelled options: ["A. Paris", "B. London", ...]
    labelled_options = [f"{chr(65+i)}. {opt}" for i, opt in enumerate(mcq.options)]

    # Restore previous selection if user came back to this question
    prev_index = st.session_state.user_answers[index]
    default    = prev_index if prev_index >= 0 else 0

    selected = st.radio(
        label     = "Select your answer:",
        options   = labelled_options,
        index     = default,
        key       = f"q_{index}",
        label_visibility = "collapsed",
    )

    # Return just the letter ("A", "B", etc.)
    return selected[0] if selected else None


def render_result_card(result: dict, question_num: int):
    """
    Render a single question's result with colour coding.
    Green = correct, Red = wrong.
    """
    is_correct = result["is_correct"]
    icon       = "✅" if is_correct else "❌"
    color      = "#d4edda" if is_correct else "#f8d7da"
    border     = "#28a745" if is_correct else "#dc3545"

    with st.container():
        st.markdown(
            f"""
            <div style="
                background-color: {color};
                border-left: 4px solid {border};
                padding: 12px 16px;
                border-radius: 6px;
                margin-bottom: 12px;
            ">
                <b>{icon} Q{question_num}: {result['question']}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Your answer:** {result['your_answer']}")
        with col2:
            if not is_correct:
                st.write(f"**Correct answer:** {result['correct_answer']}")
            else:
                st.write("**Correct!**")

        with st.expander("See explanation"):
            st.info(result["explanation"])


def render_score_summary(result: dict):
    """
    Render the score banner at the top of the results screen.
    """
    score      = result["score"]
    total      = result["total"]
    percentage = result["percentage"]
    feedback   = result["feedback"]

    # Choose colour based on score
    if percentage >= 80:
        color = "#d4edda"; border = "#28a745"
    elif percentage >= 60:
        color = "#fff3cd"; border = "#ffc107"
    else:
        color = "#f8d7da"; border = "#dc3545"

    st.markdown(
        f"""
        <div style="
            background-color: {color};
            border: 2px solid {border};
            border-radius: 10px;
            padding: 20px 24px;
            text-align: center;
        ">
            <h2 style="margin:0">{score} / {total}</h2>
            <h4 style="margin:4px 0">{percentage}%</h4>
            <p style="margin:0; color: #555">{feedback}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Metric columns for quick glance
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Correct",   score)
    c2.metric("Wrong",     total - score)
    c3.metric("Score",     f"{percentage}%")