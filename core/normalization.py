from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from config import COLUMN_OVERRIDES, EXCLUDE_SHEETS, INCLUDE_SHEETS
from core.models import NormalizationReport, SourceRef, WordEntry


WORD_HINTS = {"word", "term", "vocab", "entry"}
MEANING_HINTS = {"meaning", "definition", "gloss", "sense"}
EXAMPLE_HINTS = {"example", "sentence", "usage"}
MNEMONIC_HINTS = {"mnemonic", "memory", "hint", "trick"}
POS_HINTS = {"pos", "part of speech", "part_of_speech"}
SUBCATEGORY_HINTS = {"set", "group", "band", "level", "frequency", "category", "subcategory"}
SYNONYM_HINTS = {"synonym", "synonyms"}
FREQUENCY_PATTERN = re.compile(
    r"^\s*([1-7])\s*occur[a-z]*\s*(/s)?\s*$",
    re.IGNORECASE,
)


def _normalize_header(header: Any) -> str:
    if header is None:
        return ""
    return str(header).strip().lower()


def _score_header(header: str, hints: set[str]) -> int:
    score = 0
    for hint in hints:
        if hint in header:
            score += 2
    if header in hints:
        score += 3
    return score


def _detect_columns(columns: list[Any]) -> dict[str, str | None]:
    headers = [_normalize_header(col) for col in columns]
    mapping: dict[str, str | None] = {
        "word": None,
        "meaning": None,
        "example": None,
        "mnemonic": None,
        "pos": None,
        "subcategory": None,
        "synonyms": None,
    }

    def best_match(hints: set[str]) -> str | None:
        best_header = None
        best_score = 0
        for header in headers:
            score = _score_header(header, hints)
            if score > best_score:
                best_score = score
                best_header = header
        if best_score == 0:
            return None
        return best_header

    mapping["word"] = best_match(WORD_HINTS)
    mapping["meaning"] = best_match(MEANING_HINTS)
    mapping["example"] = best_match(EXAMPLE_HINTS)
    mapping["mnemonic"] = best_match(MNEMONIC_HINTS)
    mapping["pos"] = best_match(POS_HINTS)
    mapping["subcategory"] = best_match(SUBCATEGORY_HINTS)
    mapping["synonyms"] = best_match(SYNONYM_HINTS)

    return mapping


def _column_by_fallback(columns: list[Any], index: int) -> str | None:
    if index >= len(columns):
        return None
    col = columns[index]
    return col


def _get_sheet_names(excel_path: str, resolved_path: str) -> list[str]:
    excel_file = pd.ExcelFile(resolved_path)
    sheet_names = excel_file.sheet_names
    include = INCLUDE_SHEETS.get(excel_path) or INCLUDE_SHEETS.get(resolved_path)
    exclude = EXCLUDE_SHEETS.get(excel_path) or EXCLUDE_SHEETS.get(resolved_path, [])

    if include:
        sheet_names = [sheet for sheet in sheet_names if sheet in include]
    if exclude:
        sheet_names = [sheet for sheet in sheet_names if sheet not in exclude]
    return sheet_names


def _clean_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def _split_synonyms(value: str | None) -> list[str]:
    if not value:
        return []
    parts = re.split(r"[;,/]", value)
    cleaned = [part.strip() for part in parts if part.strip()]
    return cleaned


def _split_mnemonics(value: str | None) -> list[str]:
    if not value:
        return []
    parts = re.split(r"\n|;", value)
    cleaned = [part.strip() for part in parts if part.strip()]
    return cleaned


def _frequency_columns(columns: list[Any]) -> list[Any]:
    matches = []
    for col in columns:
        header = _normalize_header(col)
        if FREQUENCY_PATTERN.match(header):
            matches.append(col)
    return matches


def _frequency_from_first_row(df: pd.DataFrame) -> list[tuple[Any, str]]:
    if df.empty:
        return []
    first_row = df.iloc[0]
    matches: list[tuple[Any, str]] = []
    for col in df.columns:
        value = _clean_value(first_row.get(col))
        if value and FREQUENCY_PATTERN.match(value):
            matches.append((col, value))
    return matches


def _resolve_column_name(columns: list[Any], header: str | None) -> Any | None:
    if header is None:
        return None
    for col in columns:
        if _normalize_header(col) == header:
            return col
    return None


def _build_entry_from_row(
    row: pd.Series,
    columns: list[Any],
    mapping: dict[str, str | None],
    source: SourceRef,
) -> WordEntry | None:
    word_col = _resolve_column_name(columns, mapping["word"]) or _column_by_fallback(columns, 0)
    if word_col is None:
        return None
    word = _clean_value(row.get(word_col))
    if not word:
        return None

    meaning_col = _resolve_column_name(columns, mapping["meaning"]) or _column_by_fallback(columns, 1)
    example_col = _resolve_column_name(columns, mapping["example"]) or _column_by_fallback(columns, 2)
    mnemonic_col = _resolve_column_name(columns, mapping["mnemonic"]) or _column_by_fallback(columns, 3)
    pos_col = _resolve_column_name(columns, mapping["pos"]) or _column_by_fallback(columns, 4)
    subcategory_col = _resolve_column_name(columns, mapping["subcategory"]) or _column_by_fallback(columns, 5)
    synonym_col = _resolve_column_name(columns, mapping["synonyms"])

    meaning = _clean_value(row.get(meaning_col))
    example = _clean_value(row.get(example_col))
    mnemonic = _clean_value(row.get(mnemonic_col))
    pos = _clean_value(row.get(pos_col))
    subcategory = _clean_value(row.get(subcategory_col))
    synonym_value = _clean_value(row.get(synonym_col))

    source_ref = SourceRef(filename=source.filename, sheet=source.sheet, subcategory=subcategory)

    return WordEntry(
        word=word.strip(),
        meaning=meaning,
        example=example,
        pos=pos,
        synonyms=_split_synonyms(synonym_value),
        mnemonics=_split_mnemonics(mnemonic),
        sources=[source_ref],
    )


def _merge_entries(existing: WordEntry, incoming: WordEntry) -> WordEntry:
    if not existing.meaning and incoming.meaning:
        existing.meaning = incoming.meaning
    if not existing.example and incoming.example:
        existing.example = incoming.example
    if not existing.pos and incoming.pos:
        existing.pos = incoming.pos

    for synonym in incoming.synonyms:
        if synonym not in existing.synonyms:
            existing.synonyms.append(synonym)

    for mnemonic in incoming.mnemonics:
        if mnemonic not in existing.mnemonics:
            existing.mnemonics.append(mnemonic)

    existing.sources.extend(incoming.sources)
    return existing


def normalize_excel_files(excel_files: list[str]) -> tuple[list[WordEntry], NormalizationReport]:
    entries_by_word: dict[str, WordEntry] = {}
    total_rows = 0
    total_words = 0
    source_counts: Counter[str] = Counter()
    sheet_counts: Counter[str] = Counter()
    missing_files: list[str] = []
    repo_root = Path(__file__).resolve().parents[1]

    for excel_path in excel_files:
        file_path = Path(excel_path)
        if not file_path.is_absolute():
            file_path = (repo_root / file_path).resolve()
        if not file_path.exists():
            missing_files.append(str(file_path))
            continue

        for sheet in _get_sheet_names(excel_path, str(file_path)):
            overrides = COLUMN_OVERRIDES.get(excel_path, {}).get(sheet, {})
            overrides = overrides or COLUMN_OVERRIDES.get(str(file_path), {}).get(sheet, {})
            df = pd.read_excel(str(file_path), sheet_name=sheet, engine="openpyxl")
            df = df.dropna(how="all")
            if df.empty:
                continue

            columns = list(df.columns)
            if file_path.name == "GREVocabPrepSources.xlsx":
                freq_cols = _frequency_columns(columns)
                freq_first_row = _frequency_from_first_row(df)
                if freq_cols or freq_first_row:
                    if freq_cols:
                        freq_targets = [(col, _clean_value(col), False) for col in freq_cols]
                    else:
                        freq_targets = [(col, label, True) for col, label in freq_first_row]

                    for col, label, skip_first in freq_targets:
                        subcategory = _clean_value(label)
                        if not subcategory:
                            continue
                        values = df[col].tolist()
                        if skip_first:
                            values = values[1:]
                        for value in values:
                            word = _clean_value(value)
                            if not word:
                                continue
                            total_rows += 1
                            total_words += 1
                            entry = WordEntry(
                                word=word.strip(),
                                sources=[
                                    SourceRef(
                                        filename=file_path.name,
                                        sheet=sheet,
                                        subcategory=subcategory,
                                    )
                                ],
                            )
                            key = entry.word.strip().lower()
                            if key in entries_by_word:
                                entries_by_word[key] = _merge_entries(entries_by_word[key], entry)
                            else:
                                entries_by_word[key] = entry

                            source_counts[file_path.name] += 1
                            sheet_counts[f"{file_path.name}::{sheet}"] += 1
                    continue

            mapping = _detect_columns(columns)
            mapping.update({key: _normalize_header(val) for key, val in overrides.items() if val})

            for _, row in df.iterrows():
                total_rows += 1
                source = SourceRef(filename=file_path.name, sheet=sheet)
                entry = _build_entry_from_row(row, columns, mapping, source)
                if not entry:
                    continue
                total_words += 1
                key = entry.word.strip().lower()
                if key in entries_by_word:
                    entries_by_word[key] = _merge_entries(entries_by_word[key], entry)
                else:
                    entries_by_word[key] = entry

                source_counts[file_path.name] += 1
                sheet_counts[f"{file_path.name}::{sheet}"] += 1

    entries = list(entries_by_word.values())
    report = _build_report(entries, total_rows, total_words, source_counts, sheet_counts, missing_files)
    return entries, report


def _build_report(
    entries: list[WordEntry],
    total_rows: int,
    total_words: int,
    source_counts: Counter[str],
    sheet_counts: Counter[str],
    missing_files: list[str],
) -> NormalizationReport:
    missing_meaning = sum(1 for entry in entries if not entry.meaning)
    missing_example = sum(1 for entry in entries if not entry.example)
    missing_pos = sum(1 for entry in entries if not entry.pos)
    missing_mnemonic = sum(1 for entry in entries if not entry.mnemonics)
    missing_synonyms = sum(1 for entry in entries if not entry.synonyms)

    return NormalizationReport(
        total_rows=total_rows,
        total_words=total_words,
        deduped_words=len(entries),
        missing_meaning=missing_meaning,
        missing_example=missing_example,
        missing_pos=missing_pos,
        missing_mnemonic=missing_mnemonic,
        missing_synonyms=missing_synonyms,
        source_counts=dict(source_counts),
        sheet_counts=dict(sheet_counts),
        missing_files=missing_files,
    )
