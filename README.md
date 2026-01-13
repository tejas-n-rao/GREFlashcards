# GRE Vocab Studio

Local, offline-first GRE vocabulary flashcards with spaced repetition and optional enrichment.

## Setup

1) Activate the provided venv (or your own):

```bash
source gre/bin/activate
```

2) Install dependencies:

```bash
pip install streamlit pandas openpyxl nltk openai
```

3) (Optional) Download WordNet for offline enrichment:

```bash
python -m nltk.downloader wordnet
```

4) Update `config.py` with absolute paths to your Excel files.

## Run

```bash
streamlit run app/Home.py
```

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
