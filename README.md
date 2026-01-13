# GRE Vocab Studio

Local, offline-first GRE vocabulary flashcards with spaced repetition and optional enrichment. The app ingests multiple Excel files, deduplicates words case-insensitively, preserves provenance, and provides per-source and pooled study sets.

## Setup

1) Activate the provided venv (or your own):

```bash
source gre/bin/activate
```

2) Install dependencies:

```bash
pip install streamlit pandas openpyxl nltk openai pytest
```

3) (Optional) Download WordNet for offline enrichment:

```bash
python -m nltk.downloader wordnet
```

4) Update `config.py` with absolute paths to your Excel files (`EXCEL_FILES`).

## Run

```bash
streamlit run app/Home.py
```

## Configuration

- `EXCEL_FILES`: absolute file paths to `.xlsx` vocab sources.
- `INCLUDE_SHEETS` / `EXCLUDE_SHEETS`: per-file sheet controls.
- `COLUMN_OVERRIDES`: per-file per-sheet column mappings when heuristics fail.
- `ENABLE_OPENAI_ENRICHMENT`: toggle OpenAI enrichment.
- `OPENAI_MODEL`, `MAX_OPENAI_CALLS_PER_RUN`, `ENRICH_ONLY_WHEN_MISSING`: OpenAI settings.
- `SET_CHUNK_SIZE`: number of words per fixed set.
- `SET_SHUFFLE_SEED`: seed for deterministic shuffling.

## Features

- Flashcards show: word, meaning, POS, synonyms (up to 3), example, source, mnemonics.
- Card sets: per file, per sheet, optional subcategory, plus pooled.
- Spaced repetition: Again / Hard / Good / Easy (SM-2-like scheduling).
- Dashboard: due counts, accuracy, weak words, search.
- Word detail editing with optional per-word enrichment refresh.

## Data Outputs

- `data/normalized_vocab.json`: canonical merged dataset + provenance
- `data/progress.json`: SRS state and stats
- `data/enrichment_cache.json`: cached enrichment results

## Tests

```bash
pytest -q
```

## Notes

- OpenAI enrichment is disabled by default. Toggle `ENABLE_OPENAI_ENRICHMENT` in `config.py` and set `OPENAI_API_KEY` if needed.
- Excel sheets are ingested with heuristics; use `COLUMN_OVERRIDES` in `config.py` for precise mappings.
