# Repository Guidelines

This repository is a compact set of GRE study assets. It currently contains data files (Excel vocabulary lists) and a local Python virtual environment. Keep contributions focused on maintaining clean, well-labeled study materials and any supporting scripts you add.

## Project Structure & Module Organization

- `VocabList/` stores vocabulary sources in `.xlsx` format (for example, `VocabList/Magoosh1000Words.xlsx`). Keep new lists here and use descriptive filenames.
- `gre/` is a local Python virtual environment. Treat it as tooling, not source code.
- Root-level docs (including `AGENTS.md`) describe how to work in this repo.

## Build, Test, and Development Commands

No build or test scripts are defined in this repository. If you add automation, document it here and in any README.

If you add Python scripts, typical local setup would be:

```bash
source gre/bin/activate
python path/to/script.py
```

## Coding Style & Naming Conventions

There is no source code style enforced yet. When adding scripts:

- Prefer 4-space indentation and `snake_case` for Python.
- Place scripts in a dedicated folder such as `scripts/`.
- Name data files with clear, descriptive titles (for example, `VocabList/SourceName_YYYY.xlsx`).

## Testing Guidelines

No tests or test frameworks are present. If you introduce code, add a minimal test suite and keep it close to the code (for example, `tests/test_*.py`). Document the test command you expect contributors to run.

## Commit & Pull Request Guidelines

This directory is not a Git repository, so there is no commit history to infer conventions from. If you initialize Git, use concise, imperative commit messages (for example, "Add Barron word list") and keep PRs focused.

For changes to vocabulary lists, include:

- The source of the data (link or citation).
- A brief summary of what changed (new list, corrections, deduping).
- A small sample of rows if the change is substantial.

## Data Handling Notes

Excel files are binary. Avoid manual, one-off edits when possible; instead, prefer scripted transformations that can be re-run and reviewed.
