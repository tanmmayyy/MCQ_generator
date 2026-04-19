# ─────────────────────────────────────────────
#  src/evaluator.py
#  Checks user answers and computes scores.
#  Simple but important — this is what makes
#  the project interactive and demo-worthy.
# ─────────────────────────────────────────────

from src.mcq_builder import MCQ


# ─────────────────────────────────────────────
#  CHECK A SINGLE ANSWER
# ─────────────────────────────────────────────

def check_answer(mcq: MCQ, user_choice: int) -> bool:
    """
    Check if the user's selected option index is correct.
    
    Parameters:
        mcq         : the MCQ object
        user_choice : index 0-3 that the user selected
    
    Returns: True if correct, False otherwise
    """
    return user_choice == mcq.correct_index


# ─────────────────────────────────────────────
#  SCORE A FULL QUIZ
# ─────────────────────────────────────────────

def score_quiz(mcqs: list[MCQ], user_answers: list[int]) -> dict:
    """
    Score all questions and return a detailed results dict.
    
    Parameters:
        mcqs         : list of MCQ objects (the quiz)
        user_answers : list of int indices (user's selections, one per MCQ)
    
    Returns:
        {
          "score"      : 7,           ← number correct
          "total"      : 10,          ← total questions
          "percentage" : 70.0,
          "results"    : [            ← per-question details
            {
              "question"      : "In what year was ISRO founded?",
              "your_answer"   : "1975",
              "correct_answer": "1969",
              "is_correct"    : False,
              "explanation"   : "ISRO was founded in 1969 by Vikram Sarabhai.",
            },
            ...
          ]
        }
    """
    score   = 0
    results = []

    for i, (mcq, user_choice) in enumerate(zip(mcqs, user_answers)):
        is_correct = check_answer(mcq, user_choice)
        if is_correct:
            score += 1

        results.append({
            "question"       : mcq.question,
            "your_answer"    : mcq.options[user_choice] if 0 <= user_choice < len(mcq.options) else "No answer",
            "correct_answer" : mcq.correct_answer,
            "is_correct"     : is_correct,
            "explanation"    : mcq.explanation,
            "all_options"    : mcq.options,
            "correct_index"  : mcq.correct_index,
            "user_index"     : user_choice,
        })

    total      = len(mcqs)
    percentage = round((score / total) * 100, 1) if total > 0 else 0.0

    # Provide a feedback message based on score
    if percentage >= 80:
        feedback = "Excellent! You have a strong understanding of this passage."
    elif percentage >= 60:
        feedback = "Good effort! Review the explanations for questions you missed."
    elif percentage >= 40:
        feedback = "Fair attempt. Try re-reading the passage and retaking the quiz."
    else:
        feedback = "Keep practising! The explanations below will help you understand."

    return {
        "score"      : score,
        "total"      : total,
        "percentage" : percentage,
        "feedback"   : feedback,
        "results"    : results,
    }


# ─────────────────────────────────────────────
#  QUICK TEST
#  python src/evaluator.py
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Simulate 3 MCQs without running the full pipeline
    fake_mcqs = [
        MCQ("What year was ISRO founded?",
            ["1969", "1975", "1947", "1985"], 0, "1969",
            "ISRO was founded in 1969 by Vikram Sarabhai."),
        MCQ("Who founded ISRO?",
            ["Kalam", "Vikram Sarabhai", "Nehru", "Dhawan"], 1, "Vikram Sarabhai",
            "ISRO was founded in 1969 by Vikram Sarabhai."),
        MCQ("What did Chandrayaan-1 discover?",
            ["Oxygen", "Iron", "Water molecules", "Helium"], 2, "Water molecules",
            "Chandrayaan-1 discovered water molecules on the Moon."),
    ]

    # Simulate user answers: Q1 correct, Q2 wrong, Q3 correct
    user_answers = [0, 0, 2]

    result = score_quiz(fake_mcqs, user_answers)

    print("=== QUIZ RESULTS ===")
    print(f"Score: {result['score']} / {result['total']} ({result['percentage']}%)")
    print(f"Feedback: {result['feedback']}\n")
    for i, r in enumerate(result['results'], 1):
        status = "CORRECT" if r['is_correct'] else "WRONG"
        print(f"Q{i} [{status}] {r['question']}")
        print(f"     Your answer   : {r['your_answer']}")
        if not r['is_correct']:
            print(f"     Correct answer: {r['correct_answer']}")
        print(f"     Explanation   : {r['explanation'][:80]}...")
        print()