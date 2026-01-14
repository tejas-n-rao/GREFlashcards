from __future__ import annotations

from pathlib import Path

# Update these absolute paths to your local Excel files.
EXCEL_FILES = [
    "VocabList/GREVocabPrepSources.xlsx",
    "VocabList/Magoosh1000Words.xlsx",
    "VocabList/VocabMountain.xlsx",
]

# Optional include/exclude sheet configuration.
# Example:
# INCLUDE_SHEETS = {
#     "/ABS/PATH/file1.xlsx": ["Sheet1", "Sheet2"],
# }
# EXCLUDE_SHEETS = {
#     "/ABS/PATH/file2.xlsx": ["Archive"],
# }
INCLUDE_SHEETS: dict[str, list[str]] = {
    "VocabList/VocabMountain.xlsx": ["Day 32"],
}
EXCLUDE_SHEETS: dict[str, list[str]] = {}

# Manual column mapping per file/sheet if heuristics fail.
# Example:
# COLUMN_OVERRIDES = {
#     "/ABS/PATH/file1.xlsx": {
#         "Sheet1": {
#             "word": "Word",
#             "meaning": "Meaning",
#             "example": "Example",
#             "mnemonic": "Mnemonic",
#             "subcategory": "Set",
#             "pos": "POS",
#         }
#     }
# }
COLUMN_OVERRIDES: dict[str, dict[str, dict[str, str]]] = {}

# Enrichment toggles
ENABLE_OPENAI_ENRICHMENT = False
OPENAI_MODEL = "gpt-4o-mini"
MAX_OPENAI_CALLS_PER_RUN = 100
ENRICH_ONLY_WHEN_MISSING = True

# Data paths
DATA_DIR = Path("data")
NORMALIZED_VOCAB_PATH = DATA_DIR / "normalized_vocab.json"
PROGRESS_PATH = DATA_DIR / "progress.json"
ENRICHMENT_CACHE_PATH = DATA_DIR / "enrichment_cache.json"
CUSTOM_DECKS_PATH = DATA_DIR / "custom_decks.json"

# App defaults
DEFAULT_ACTIVE_SET = "Pooled"
NEW_CARDS_PER_SESSION = 20
EXTRA_CARDS_PER_SESSION = 10
SET_CHUNK_SIZE = 50
SET_SHUFFLE_SEED = 42
