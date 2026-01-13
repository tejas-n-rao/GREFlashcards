from core.models import SourceRef, WordEntry
from core.normalization import _merge_entries


def test_merge_entries_prefers_non_empty_fields():
    base = WordEntry(
        word="Abate",
        meaning=None,
        example=None,
        pos=None,
        synonyms=["decrease"],
        mnemonics=[],
        sources=[SourceRef(filename="A.xlsx", sheet="Sheet1")],
    )
    incoming = WordEntry(
        word="abate",
        meaning="to reduce",
        example="The storm abated.",
        pos="Verb",
        synonyms=["diminish"],
        mnemonics=["a bait gets less"],
        sources=[SourceRef(filename="B.xlsx", sheet="Sheet2")],
    )

    merged = _merge_entries(base, incoming)
    assert merged.meaning == "to reduce"
    assert merged.example == "The storm abated."
    assert merged.pos == "Verb"
    assert "decrease" in merged.synonyms
    assert "diminish" in merged.synonyms
    assert merged.mnemonics == ["a bait gets less"]
    assert len(merged.sources) == 2
