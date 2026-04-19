# ─────────────────────────────────────────────
#  src/distractor_generator.py  (v3)
#  Distractors MUST be the same entity type
#  as the correct answer.
#  e.g. answer=PERSON → distractors are PERSONs
#       answer=DATE   → distractors are DATEs
# ─────────────────────────────────────────────

import random
import sys, os

import nltk
from nltk.corpus import wordnet

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NUM_DISTRACTORS

nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)


def get_same_label_distractors(answer: str, answer_label: str,
                                all_entities: list, n: int) -> list:
    """
    Find entities from the passage that have the SAME NER label as the answer.
    This ensures distractors are always the same type as the answer.

    all_entities is a list of {"text": str, "label": str} dicts.
    """
    distractors = []
    seen = {answer.lower()}

    # First pass: exact same label
    for ent in all_entities:
        if ent["label"] == answer_label and ent["text"].lower() not in seen:
            distractors.append(ent["text"])
            seen.add(ent["text"].lower())

    return distractors[:n]


def get_wordnet_distractors(answer: str, n: int) -> list:
    """WordNet hyponym siblings — same semantic category."""
    answer_key  = answer.lower().replace(" ", "_")
    distractors = set()

    synsets = wordnet.synsets(answer_key)
    if not synsets:
        for word in answer.split():
            synsets += wordnet.synsets(word.lower())

    for synset in synsets[:5]:
        for hypernym in synset.hypernyms():
            for hyponym in hypernym.hyponyms():
                for lemma in hyponym.lemma_names():
                    word = lemma.replace("_", " ")
                    if word.lower() == answer.lower():
                        continue
                    if len(word) > 1:
                        distractors.add(word.title() if answer[0].isupper() else word)
        if len(distractors) >= n * 3:
            break

    result = list(distractors)
    random.shuffle(result)
    return result[:n]


def get_distractors(answer: str, all_entities: list,
                     passage_doc=None, n: int = NUM_DISTRACTORS) -> list:
    """
    Main distractor function.
    Strategy:
      1. Same-label entities from the passage  (best — contextual + same type)
      2. WordNet siblings                       (good for common nouns)
      3. Cross-label entities from passage      (last resort, still real words)
    Never mixes types if same-label gives enough results.
    """
    collected = []
    seen      = {answer.lower()}

    def add(candidates):
        for c in candidates:
            if isinstance(c, dict):
                text = c["text"]
            else:
                text = c
            if text.lower() not in seen and text.lower() != answer.lower():
                seen.add(text.lower())
                collected.append(text)

    # Find the answer's NER label from the entity list
    answer_label = ""
    for ent in all_entities:
        if ent["text"].lower() == answer.lower():
            answer_label = ent["label"]
            break
    # Fuzzy match if exact not found
    if not answer_label:
        for ent in all_entities:
            if answer.lower() in ent["text"].lower():
                answer_label = ent["label"]
                break

    # Strategy 1: same label from passage
    add(get_same_label_distractors(answer, answer_label, all_entities, n * 2))

    # Strategy 2: WordNet
    if len(collected) < n:
        add(get_wordnet_distractors(answer, n * 2))

    # Strategy 3: any other passage entity (cross-label fallback)
    if len(collected) < n:
        add(all_entities)   # add() handles dedup

    # Only if still short, add generic placeholders
    placeholders = ["None of the above", "Cannot be determined", "All of the above"]
    for p in placeholders:
        if len(collected) >= n:
            break
        if p not in collected:
            collected.append(p)

    return collected[:n]


if __name__ == "__main__":
    # Simulate entity list from preprocessor
    entities = [
        {"text": "ISRO",            "label": "ORG"},
        {"text": "NASA",            "label": "ORG"},
        {"text": "ESA",             "label": "ORG"},
        {"text": "Vikram Sarabhai", "label": "PERSON"},
        {"text": "Vince McMahon",   "label": "PERSON"},
        {"text": "John Cena",       "label": "PERSON"},
        {"text": "1969",            "label": "DATE"},
        {"text": "1975",            "label": "DATE"},
        {"text": "2008",            "label": "DATE"},
        {"text": "India",           "label": "GPE"},
        {"text": "United States",   "label": "GPE"},
        {"text": "China",           "label": "GPE"},
    ]

    tests = [
        ("Vikram Sarabhai", "PERSON"),
        ("1969",            "DATE"),
        ("India",           "GPE"),
        ("ISRO",            "ORG"),
    ]

    print("=== DISTRACTOR TEST ===\n")
    for answer, label in tests:
        d = get_distractors(answer, entities)
        print(f"  Answer ({label:8s}): {answer:20s} → {d}")