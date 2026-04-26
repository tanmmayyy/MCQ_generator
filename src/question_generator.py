# ─────────────────────────────────────────────
#  src/question_generator.py  (v4)
#  Key fix: validate that the generated question
#  actually targets the intended answer.
#  Also filters circular questions like
#  "What is the name of X?" when answer IS X.
# ─────────────────────────────────────────────

from transformers import pipeline
import re
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import QG_MODEL_NAME, MAX_QUESTIONS

print(f"[INFO] Loading QG model: {QG_MODEL_NAME} ...")
import warnings
warnings.filterwarnings("ignore")   # suppress HuggingFace FutureWarnings



try:
    qg_pipeline = pipeline(
        "text2text-generation",
        model     = QG_MODEL_NAME,
        tokenizer = QG_MODEL_NAME,
    )
    print("[INFO] Model loaded.")
except Exception as e:
    print(f"[ERROR] {e}")
    raise


def highlight_answer(sentence: str, answer: str) -> str:
    """Wrap answer with <hl> tags for the T5 model."""
    pattern = re.compile(re.escape(answer), re.IGNORECASE)
    result  = pattern.sub(f"<hl> {answer} <hl>", sentence, count=1)
    return result


def answer_is_addressable(question: str, answer: str) -> bool:
    """
    Check that the question is actually ASKING FOR the answer.
    
    Rejects:
    - Circular: answer text appears in the question
      e.g. Q: "What is the name of ISRO?" A: "The Indian Space Research Organisation"
           (ISRO is an abbreviation of the answer — circular)
    - Too vague: question is only 4 words or fewer
    - No question word
    - Answer is a substring of the question
    """
    q = question.strip()
    a = answer.strip()

    # Must end with ?
    if not q.endswith("?"):
        return False

    # Must have a question word
    q_lower = q.lower()
    if not any(q_lower.startswith(w) for w in
               ["what", "who", "when", "where", "which", "how", "why"]):
        return False

    # Must be at least 5 words
    if len(q.split()) < 5:
        return False

    # Answer must NOT appear verbatim in the question
    if a.lower() in q_lower:
        return False

    # Check abbreviation trap: if any word in the question is an abbreviation
    # of the answer (e.g. "ISRO" in question, answer is "Indian Space Research...")
    answer_words = [w.lower() for w in a.split() if len(w) > 1]
    abbrev = "".join(w[0] for w in answer_words if w.isalpha())
    if len(abbrev) >= 2 and abbrev.lower() in q_lower:
        return False

    # Reject questions asking about name/abbreviation — usually circular
    circular_patterns = [
        r"what (is|was|were) the (full |official )?name",
        r"what (does|did) .{1,10} stand for",
        r"what (is|was) the abbreviation",
        r"what (is|was) .{1,15} also (known|called)",
    ]
    for pat in circular_patterns:
        if re.search(pat, q_lower):
            return False

    return True


def generate_question(sentence: str, answer: str) -> str | None:
    """
    Generate a question for a (sentence, answer) pair.
    Returns the best valid question string, or None.
    """
    highlighted = highlight_answer(sentence, answer)
    input_text  = f"generate question: {highlighted}"

    try:
        outputs = qg_pipeline(
            input_text,
            max_new_tokens       = 64,
            num_beams            = 5,
            num_return_sequences = 3,
            early_stopping       = True,
        )
    except Exception as e:
        print(f"  [QG] Generation error: {e}")
        return None

    for output in outputs:
        q = output["generated_text"].strip()
        if not q.endswith("?"):
            q += "?"
        if answer_is_addressable(q, answer):
            return q

    return None


def generate_questions(sentence_answers: dict) -> list:
    """
    For each (sentence → answer candidates), generate one good question.
    Tries each answer candidate in priority order until one works.
    """
    results = []

    for sentence, candidates in sentence_answers.items():
        if len(results) >= MAX_QUESTIONS:
            break

        generated = False
        for answer in candidates:
            if len(answer.strip()) < 2:
                continue

            question = generate_question(sentence, answer)

            if question:
                print(f"  [QG] ✓ Q: {question}")
                print(f"         A: {answer}")
                results.append({
                    "question" : question,
                    "answer"   : answer,
                    "sentence" : sentence,
                })
                generated = True
                break
            else:
                print(f"  [QG] ✗ Rejected for answer '{answer}'")

        if not generated:
            print(f"  [QG] — No valid question for: '{sentence[:60]}'")

    return results


if __name__ == "__main__":
    tests = [
        # Good cases — specific named answers
        ("ISRO was founded in 1969 by Vikram Sarabhai.", "Vikram Sarabhai"),
        ("Aryabhata was India's first satellite, launched in 1975.", "Aryabhata"),
        ("The Chandrayaan-1 mission in 2008 discovered water on the Moon.", "2008"),
        ("Chandrayaan-3 landed near the lunar south pole in 2023.", "Chandrayaan-3"),
        ("The Taj Mahal was built by Shah Jahan in 1632 in Agra.", "Shah Jahan"),
        # Bad cases — should all be rejected
        ("The Indian Space Research Organisation (ISRO) was founded in 1969.", "The Indian Space Research Organisation"),
        ("ISRO developed India's first satellite.", "India"),
    ]

    print("\n=== QUESTION GENERATION TEST ===\n")
    for sentence, answer in tests:
        q = generate_question(sentence, answer)
        status = "✓" if q else "✗ (rejected)"
        print(f"  [{status}]")
        print(f"    Sentence: {sentence}")
        print(f"    Answer  : {answer}")
        print(f"    Question: {q}\n")