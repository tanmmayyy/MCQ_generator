# ─────────────────────────────────────────────
#  config.py  –  Central settings for MCQ Generator
#  Change values here to tune the whole project.
# ─────────────────────────────────────────────

# ── Model settings ──────────────────────────
# T5 model fine-tuned on SQuAD for question generation
# "highlight" format: answer is wrapped in <hl> tags in the input
QG_MODEL_NAME = "valhalla/t5-small-qg-hl"

# spaCy English model for NLP preprocessing
SPACY_MODEL = "en_core_web_sm"

# ── Pipeline settings ───────────────────────
# How many top-ranked sentences to pick questions from
TOP_SENTENCES = 7

# Maximum number of MCQs to generate from one passage
MAX_QUESTIONS = 10

# Minimum sentence length (in words) to be considered for a question
MIN_SENTENCE_LENGTH = 8

# Number of wrong options (distractors) per question
NUM_DISTRACTORS = 3

# ── Distractor generation strategy ──────────
# Order of strategies tried. First one that returns enough distractors wins.
# Options: "wordnet", "sense2vec", "ner"
DISTRACTOR_STRATEGIES = ["wordnet", "ner", "sense2vec"]

# ── Paths ────────────────────────────────────
# Path to GloVe vectors file (download separately if using sense2vec)
# Download: https://nlp.stanford.edu/projects/glove/
GLOVE_PATH = "models/glove.6B.100d.txt"

# Path to sample passages for testing
SAMPLE_DATA_PATH = "data/sample_passages.json"

# ── UI settings ──────────────────────────────
APP_TITLE = "MCQ Generator"
APP_ICON  = "📝"