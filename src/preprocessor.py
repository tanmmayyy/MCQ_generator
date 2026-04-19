# ─────────────────────────────────────────────
#  src/preprocessor.py  (v3)
# ─────────────────────────────────────────────

import re
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SPACY_MODEL, TOP_SENTENCES, MIN_SENTENCE_LENGTH

try:
    nlp = spacy.load(SPACY_MODEL)
except OSError:
    print(f"[ERROR] Run: python -m spacy download {SPACY_MODEL}")
    raise

# Only these NER labels make meaningful quiz answers
GOOD_NER_LABELS = {
    "PERSON", "ORG", "GPE", "LOC",
    "DATE", "EVENT", "WORK_OF_ART",
    "NORP", "FAC", "PRODUCT",
}

# Hard blacklist — never use these as answers
BLACKLIST = {
    "annual", "various", "many", "several", "some", "other",
    "new", "old", "big", "large", "small", "high", "low",
    "one", "two", "three", "four", "five", "first", "second",
    "today", "yesterday", "now", "then", "later", "also",
    "he", "she", "it", "they", "we", "i", "the", "a", "an",
    "moon", "sun", "earth",
    "india", "america", "china", "russia", "england", "world",  # too broad
    "isro", "nasa", "wwe", "un", "who",  # abbreviations make circular Qs
}

# Prefer answers with these labels — they make the clearest questions
HIGH_PRIORITY_LABELS = {"PERSON", "ORG", "GPE", "LOC", "EVENT", "WORK_OF_ART", "FAC", "PRODUCT"}


def extract_sentences(text: str) -> list:
    doc = nlp(text)
    sentences = []
    for sent in doc.sents:
        clean = sent.text.strip()
        word_count = len([t for t in sent if not t.is_space and not t.is_punct])
        if word_count >= MIN_SENTENCE_LENGTH:
            sentences.append(clean)
    return sentences


def rank_sentences(sentences: list, top_n: int = TOP_SENTENCES) -> list:
    if len(sentences) <= top_n:
        return sentences
    vectorizer   = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(sentences)
    scores       = np.array(tfidf_matrix.sum(axis=1)).flatten()
    top_indices  = sorted(np.argsort(scores)[::-1][:top_n])
    return [sentences[i] for i in top_indices]


def is_good_answer(text: str, label: str) -> bool:
    t = text.strip()

    if len(t) < 2:
        return False

    # Reject blacklisted words (case-insensitive)
    if t.lower() in BLACKLIST:
        return False

    # Must be an allowed NER label
    if label not in GOOD_NER_LABELS:
        return False

    # Single lowercase word with no capitals = probably not a proper noun
    if len(t.split()) == 1 and t[0].islower() and not t.isdigit():
        return False

    # Reject very long phrases (>5 words) — hard to use as MCQ answers
    if len(t.split()) > 5:
        return False

    return True


def extract_answer_candidates(sentence: str) -> list:
    """
    Extract answer candidates from a sentence.
    Returns high-priority entities first, then dates/others.
    Only ONE answer per sentence is ultimately used (the best one).
    """
    doc = nlp(sentence)

    high = []   # PERSON, ORG, GPE, etc.
    low  = []   # DATE, QUANTITY, etc.
    seen = set()

    for ent in doc.ents:
        text  = ent.text.strip()
        label = ent.label_

        if not is_good_answer(text, label):
            continue
        if text.lower() in seen:
            continue

        seen.add(text.lower())

        if label in HIGH_PRIORITY_LABELS:
            high.append(text)
        else:
            low.append(text)

    # Return high-priority first, then dates/quantities
    return high + low


def preprocess(text: str) -> dict:
    text             = re.sub(r'\s+', ' ', text).strip()
    all_sentences    = extract_sentences(text)
    top_sentences    = rank_sentences(all_sentences)
    sentence_answers = {}

    for sent in top_sentences:
        candidates = extract_answer_candidates(sent)
        if candidates:
            sentence_answers[sent] = candidates

    doc          = nlp(text)
    # Store entities WITH their labels for the distractor generator
    all_entities = []
    seen = set()
    for ent in doc.ents:
        if is_good_answer(ent.text.strip(), ent.label_) and ent.text.lower() not in seen:
            seen.add(ent.text.lower())
            all_entities.append({"text": ent.text.strip(), "label": ent.label_})

    return {
        "all_sentences"    : all_sentences,
        "top_sentences"    : top_sentences,
        "sentence_answers" : sentence_answers,
        "entities"         : all_entities,   # now list of {"text":..,"label":..}
    }


if __name__ == "__main__":
    sample = """
    The Indian Space Research Organisation (ISRO) was founded in 1969 by Vikram Sarabhai.
    ISRO developed India's first satellite, Aryabhata, which was launched in 1975.
    The Chandrayaan-1 mission in 2008 discovered water molecules on the Moon.
    In 2023, Chandrayaan-3 successfully landed near the lunar south pole, making India
    the fourth country to achieve a Moon landing.
    The Mars Orbiter Mission, also called Mangalyaan, was launched in 2013.
    """
    result = preprocess(sample)
    print("=== SENTENCE → CANDIDATES ===")
    for sent, ans in result['sentence_answers'].items():
        print(f"  Source : {sent[:75]}")
        print(f"  Answers: {ans}\n")
    print("=== ALL ENTITIES (for distractors) ===")
    for e in result['entities']:
        print(f"  {e['label']:15s} {e['text']}")