# ─────────────────────────────────────────────
#  src/mcq_builder.py  (v4)
#  Added strict MCQ quality validation.
# ─────────────────────────────────────────────

import random
from dataclasses import dataclass
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NUM_DISTRACTORS, MAX_QUESTIONS

from src.preprocessor         import preprocess
from src.question_generator   import generate_questions
from src.distractor_generator import get_distractors


@dataclass
class MCQ:
    question       : str
    options        : list
    correct_index  : int
    correct_answer : str
    explanation    : str

    def display(self):
        print(f"\nQ: {self.question}")
        for i, opt in enumerate(self.options):
            marker = " ✓" if i == self.correct_index else ""
            print(f"   {chr(65+i)}. {opt}{marker}")
        print(f"   Explanation: {self.explanation[:100]}...")


def are_too_similar(a: str, b: str) -> bool:
    """
    Check if two option strings are too similar to coexist in the same MCQ.
    Handles cases like "WWE" vs "World Wrestling Entertainment",
    or "ISRO" vs "Indian Space Research Organisation".
    """
    a_lower = a.lower().strip()
    b_lower = b.lower().strip()

    # Exact match
    if a_lower == b_lower:
        return True

    # One is a substring of the other (e.g. "WWE" in "WWE Championship")
    if a_lower in b_lower or b_lower in a_lower:
        return True

    # Check word overlap ratio — if 60%+ words overlap, too similar
    words_a = set(a_lower.split())
    words_b = set(b_lower.split())
    if not words_a or not words_b:
        return False
    overlap = len(words_a & words_b)
    smaller = min(len(words_a), len(words_b))
    if smaller > 0 and overlap / smaller >= 0.6:
        return True

    return False


def deduplicate_options(answer: str, distractors: list) -> list:
    """
    Remove distractors that are too similar to each other or to the answer.
    Returns a clean list of unique distractors.
    """
    clean = []
    for d in distractors:
        # Skip if too similar to the correct answer
        if are_too_similar(d, answer):
            continue
        # Skip if too similar to an already-accepted distractor
        if any(are_too_similar(d, accepted) for accepted in clean):
            continue
        clean.append(d)
    return clean


def is_valid_mcq(question: str, answer: str, options: list) -> tuple:
    """
    Final quality gate before an MCQ is accepted.
    Returns (is_valid: bool, reason: str).
    """
    # Answer must appear in options exactly once
    answer_count = sum(1 for o in options if o.lower().strip() == answer.lower().strip())
    if answer_count != 1:
        return False, f"Answer appears {answer_count} times in options"

    # Must have exactly 4 options
    if len(options) != 4:
        return False, f"Only {len(options)} options"

    # No two options should be too similar
    for i in range(len(options)):
        for j in range(i + 1, len(options)):
            if are_too_similar(options[i], options[j]):
                return False, f"Options too similar: '{options[i]}' vs '{options[j]}'"

    # Generic placeholder options are a last resort — skip if more than 1
    generic = {"None of the above", "Cannot be determined",
               "All of the above", "Information not provided"}
    generic_count = sum(1 for o in options if o in generic)
    if generic_count > 1:
        return False, "Too many generic placeholder options"

    # Question should not just be asking "What is X?" where X is the answer
    q_lower = question.lower()
    a_lower = answer.lower()
    if a_lower in q_lower:
        return False, "Answer already present in question"

    return True, "OK"


def build_mcq(question: str, answer: str, distractors: list, explanation: str):
    """Build and validate one MCQ. Returns MCQ or None if quality check fails."""

    # Deduplicate distractors against each other and the answer
    clean_distractors = deduplicate_options(answer, distractors)

    if len(clean_distractors) < 1:
        return None

    # Pad to 3 if needed (after dedup we might have fewer)
    placeholders = ["None of the above", "Cannot be determined", "All of the above"]
    for p in placeholders:
        if len(clean_distractors) >= NUM_DISTRACTORS:
            break
        if p not in clean_distractors:
            clean_distractors.append(p)

    options = [answer] + clean_distractors[:NUM_DISTRACTORS]
    random.shuffle(options)
    correct_index = options.index(answer)

    # Run quality gate
    valid, reason = is_valid_mcq(question, answer, options)
    if not valid:
        print(f"  [QC] Rejected MCQ — {reason}: Q='{question[:50]}'")
        return None

    return MCQ(
        question       = question,
        options        = options,
        correct_index  = correct_index,
        correct_answer = answer,
        explanation    = explanation,
    )


def build_quiz(passage: str, num_questions: int = MAX_QUESTIONS) -> list:
    print(f"\n[Pipeline] Starting for passage ({len(passage)} chars)...")

    print("[Pipeline] Step 1/3: Preprocessing...")
    prep             = preprocess(passage)
    sentence_answers = prep["sentence_answers"]
    all_entities     = prep["entities"]

    if not sentence_answers:
        print("[Pipeline] No suitable sentences found.")
        return []

    print("[Pipeline] Step 2/3: Generating questions...")
    qa_pairs = generate_questions(sentence_answers)

    if not qa_pairs:
        print("[Pipeline] No questions generated.")
        return []

    print(f"[Pipeline] {len(qa_pairs)} candidate question(s) generated.")

    print("[Pipeline] Step 3/3: Building and validating MCQs...")
    mcqs = []

    for qa in qa_pairs:
        if len(mcqs) >= num_questions:
            break

        distractors = get_distractors(
            answer       = qa["answer"],
            all_entities = all_entities,
        )

        mcq = build_mcq(
            question    = qa["question"],
            answer      = qa["answer"],
            distractors = distractors,
            explanation = qa["sentence"],
        )

        if mcq is not None:
            mcqs.append(mcq)

    print(f"[Pipeline] Done. {len(mcqs)} valid MCQ(s) built.")

    if len(mcqs) == 0:
        print("\n[Pipeline] NOTICE: Could not build valid MCQs from this passage.")
        print("  This usually means the passage lacks specific named facts.")
        print("  Try a factual passage with: people names, places, dates, organisations.")

    return mcqs


if __name__ == "__main__":
    # Test with ISRO passage (factual — should work well)
    passage = """
    The Indian Space Research Organisation (ISRO) was founded in 1969 by Vikram Sarabhai.
    It is headquartered in Bengaluru, Karnataka. ISRO developed India's first satellite,
    Aryabhata, which was launched in 1975. The Chandrayaan-1 mission in 2008 discovered
    water molecules on the Moon. In 2023, Chandrayaan-3 successfully landed near the
    lunar south pole, making India the fourth country to achieve a Moon landing.
    The Mars Orbiter Mission, also called Mangalyaan, was launched in 2013 and made
    India the first Asian country to reach Martian orbit.
    """

    mcqs = build_quiz(passage, num_questions=5)
    print("\n========== GENERATED QUIZ ==========")
    for i, mcq in enumerate(mcqs, 1):
        print(f"\n--- Question {i} ---")
        mcq.display()