from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook


def main() -> None:
    workbook_path = Path("VocabList/VocabMountain.xlsx").resolve()
    if not workbook_path.exists():
        raise FileNotFoundError(f"Missing workbook: {workbook_path}")

    wb = load_workbook(workbook_path)
    keep_sheet = "Day 32"
    if keep_sheet not in wb.sheetnames:
        raise ValueError(f"Sheet '{keep_sheet}' not found in {workbook_path}")

    for sheet in list(wb.sheetnames):
        if sheet != keep_sheet:
            wb.remove(wb[sheet])

    wb.save(workbook_path)


if __name__ == "__main__":
    main()
