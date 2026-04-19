# ─────────────────────────────────────────────
#  app/main.py
#  Streamlit UI — the full interactive quiz app.
#
#  Run with:  streamlit run app/main.py
#
#  Three screens:
#    1. INPUT   → user pastes a passage, picks # of questions
#    2. QUIZ    → one question at a time with radio buttons
#    3. RESULTS → score + per-question feedback
# ─────────────────────────────────────────────

import streamlit as st
import sys, os

# Make sure we can import from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import APP_TITLE, APP_ICON, MAX_QUESTIONS
from src.mcq_builder import build_quiz
from src.evaluator   import score_quiz
from app.components  import render_question_card, render_result_card, render_score_summary


# ─────────────────────────────────────────────
#  PAGE CONFIG — must be first Streamlit call
# ─────────────────────────────────────────────

st.set_page_config(
    page_title = APP_TITLE,
    page_icon  = APP_ICON,
    layout     = "centered",
)


# ─────────────────────────────────────────────
#  SESSION STATE INITIALISATION
#  st.session_state persists values across reruns.
#  Think of it as the app's memory.
# ─────────────────────────────────────────────

def init_state():
    defaults = {
        "screen"       : "input",   # "input" | "quiz" | "results"
        "mcqs"         : [],        # list of MCQ objects
        "current_q"    : 0,         # index of current question
        "user_answers" : [],        # user's selected option indices
        "quiz_result"  : None,      # scored result dict
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()


# ─────────────────────────────────────────────
#  HELPER: reset to start a new quiz
# ─────────────────────────────────────────────

def reset():
    st.session_state.screen       = "input"
    st.session_state.mcqs         = []
    st.session_state.current_q    = 0
    st.session_state.user_answers = []
    st.session_state.quiz_result  = None


# ─────────────────────────────────────────────
#  SCREEN 1: INPUT
#  User pastes a passage and hits "Generate Quiz"
# ─────────────────────────────────────────────

def screen_input():
    st.title(f"{APP_ICON} {APP_TITLE}")
    st.write("Paste any text passage below to automatically generate a quiz from it.")

    st.info(
        "**For best results**, use factual passages containing: "
        "**people names, places, dates, organisations, or events.**  \n"
        "Try: history, science, geography, biographies.  \n"
        "Avoid opinion or purely descriptive text — they lack named facts."
    )

    st.markdown("---")

    passage = st.text_area(
        label       = "Your passage",
        placeholder = "Paste a paragraph or article here...",
        height      = 250,
        help        = "Minimum ~5 sentences recommended for best results.",
    )

    num_questions = st.slider(
        label   = "Number of questions",
        min_value = 3,
        max_value = MAX_QUESTIONS,
        value     = 5,
        step      = 1,
    )

    st.markdown("---")

    if st.button("Generate Quiz", type="primary", use_container_width=True):
        if not passage or len(passage.split()) < 30:
            st.warning("Please paste a longer passage (at least ~30 words).")
            return

        with st.spinner("Generating questions... this may take 30–60 seconds on first run."):
            try:
                mcqs = build_quiz(passage, num_questions=num_questions)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                return

        if not mcqs:
            st.error("Could not generate questions from this passage. Try a different text.")
            return

        # Store in session and move to quiz screen
        st.session_state.mcqs         = mcqs
        st.session_state.user_answers = [-1] * len(mcqs)  # -1 = unanswered
        st.session_state.current_q    = 0
        st.session_state.screen       = "quiz"
        st.rerun()


# ─────────────────────────────────────────────
#  SCREEN 2: QUIZ
#  One question at a time, with navigation.
# ─────────────────────────────────────────────

def screen_quiz():
    mcqs      = st.session_state.mcqs
    current   = st.session_state.current_q
    total     = len(mcqs)
    mcq       = mcqs[current]

    # Progress bar
    st.progress((current) / total, text=f"Question {current+1} of {total}")
    st.markdown("---")

    # Render the question card (defined in components.py)
    selected_label = render_question_card(mcq, current)

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    # Previous button
    with col1:
        if current > 0:
            if st.button("← Previous"):
                st.session_state.current_q -= 1
                st.rerun()

    # Next / Submit button
    with col3:
        # Convert selected label (A/B/C/D) back to index
        if selected_label:
            selected_index = ord(selected_label) - ord("A")
            st.session_state.user_answers[current] = selected_index

        if current < total - 1:
            if st.button("Next →", type="primary"):
                if selected_label is None:
                    st.warning("Please select an answer before continuing.")
                else:
                    st.session_state.current_q += 1
                    st.rerun()
        else:
            # Last question — show Submit button
            if st.button("Submit Quiz", type="primary"):
                if selected_label is None:
                    st.warning("Please select an answer before submitting.")
                else:
                    # Score the quiz
                    result = score_quiz(
                        st.session_state.mcqs,
                        st.session_state.user_answers
                    )
                    st.session_state.quiz_result = result
                    st.session_state.screen      = "results"
                    st.rerun()

    # Show quit option
    with col2:
        if st.button("Quit Quiz", help="Return to the input screen"):
            reset()
            st.rerun()


# ─────────────────────────────────────────────
#  SCREEN 3: RESULTS
#  Score summary + per-question breakdown
# ─────────────────────────────────────────────

def screen_results():
    result = st.session_state.quiz_result

    st.title("Quiz Complete!")
    st.markdown("---")

    # Score summary banner
    render_score_summary(result)

    st.markdown("---")
    st.subheader("Question-by-question breakdown")

    # Per-question result cards
    for i, r in enumerate(result["results"]):
        render_result_card(r, i + 1)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Try Another Passage", use_container_width=True):
            reset()
            st.rerun()
    with col2:
        if st.button("Retake Same Quiz", type="primary", use_container_width=True):
            # Reset answers but keep the same MCQs
            st.session_state.user_answers = [-1] * len(st.session_state.mcqs)
            st.session_state.current_q    = 0
            st.session_state.screen       = "quiz"
            st.rerun()


# ─────────────────────────────────────────────
#  ROUTER — picks which screen to show
# ─────────────────────────────────────────────

if st.session_state.screen == "input":
    screen_input()
elif st.session_state.screen == "quiz":
    screen_quiz()
elif st.session_state.screen == "results":
    screen_results()