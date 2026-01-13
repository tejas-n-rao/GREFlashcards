# Repository Guidelines

This repository is a compact set of GRE study assets plus a local Streamlit flashcard app. It contains data files (Excel vocabulary lists), a local Python virtual environment, and Python source for normalization, spaced repetition, and UI. Keep contributions focused on maintaining clean, well-labeled study materials and the supporting app/scripts.

## Project Structure & Module Organization

- `VocabList/` stores vocabulary sources in `.xlsx` format (for example, `VocabList/Magoosh1000Words.xlsx`). Keep new lists here and use descriptive filenames.
- `gre/` is a local Python virtual environment. Treat it as tooling, not source code.
- `app/` contains Streamlit pages (`Home`, `Study`, `Dashboard`, `Word Detail`, `Settings`).
- `core/` contains ingestion, normalization, enrichment, SRS scheduler, and persistence logic.
- `data/` stores generated JSON outputs (`normalized_vocab.json`, `progress.json`, `enrichment_cache.json`).
- Root-level docs (including `AGENTS.md`) describe how to work in this repo.

## Build, Test, and Development Commands

Primary commands are:

```bash
source gre/bin/activate
streamlit run app/Home.py
```

Run tests with:

```bash
pytest -q
```

## Coding Style & Naming Conventions

There is no source code style enforced yet. When adding scripts or app modules:

- Prefer 4-space indentation and `snake_case` for Python.
- Place scripts in a dedicated folder such as `scripts/`.
- Name data files with clear, descriptive titles (for example, `VocabList/SourceName_YYYY.xlsx`).

## Testing Guidelines

Minimal tests live in `tests/`. Keep new tests close to code changes and run with `pytest -q`.

## Commit & Pull Request Guidelines

This directory is not a Git repository, so there is no commit history to infer conventions from. If you initialize Git, use concise, imperative commit messages (for example, "Add Barron word list") and keep PRs focused.

For changes to vocabulary lists, include:

- The source of the data (link or citation).
- A brief summary of what changed (new list, corrections, deduping).
- A small sample of rows if the change is substantial.

## Data Handling Notes

Excel files are binary. Avoid manual, one-off edits when possible; instead, prefer scripted transformations that can be re-run and reviewed.

## App Notes

- Configuration lives in `config.py`, including `EXCEL_FILES`, sheet include/exclude, enrichment toggles, and OpenAI model settings.
- The app deduplicates words case-insensitively, preserves provenance, and stores the merged dataset in JSON.
- Enrichment is offline-first (WordNet), with optional OpenAI calls controlled by `ENABLE_OPENAI_ENRICHMENT`.
- Fixed study sets are generated per source file and for the pooled list using `SET_CHUNK_SIZE` and `SET_SHUFFLE_SEED`.
