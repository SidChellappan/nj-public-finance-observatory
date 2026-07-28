from __future__ import annotations

from njpfo import RAW_WORKBOOK, SOURCE_SHA256, TARGET_MUNICIPALITIES
from njpfo.download import ensure_source, verify_source
from njpfo.extract import read_formula_evidence

VALUATION_CELLS_2024 = {
    "1103": "LW291",
    "1107": "LW295",
    "1111": "LW297",
    "1113": "LW299",
    "1114": "LW300",
}


def test_2024_target_valuations_are_external_abstracts_vlookups() -> None:
    assert set(VALUATION_CELLS_2024) == set(TARGET_MUNICIPALITIES)
    ensure_source(RAW_WORKBOOK)
    assert verify_source(RAW_WORKBOOK) == SOURCE_SHA256

    formulas = read_formula_evidence(
        RAW_WORKBOOK,
        sheet_name="2024 Summary",
        cells_by_code=VALUATION_CELLS_2024,
    )

    assert set(formulas) == set(VALUATION_CELLS_2024)
    for code, source_cell in VALUATION_CELLS_2024.items():
        formula = formulas[code]
        normalized_formula = formula.upper()
        assert "VLOOKUP(" in normalized_formula, (
            f"2024 Summary!{source_cell} for municipality code {code} no "
            f"longer contains a VLOOKUP formula: {formula!r}"
        )
        assert "[4]ABSTRACTS!" in normalized_formula, (
            f"2024 Summary!{source_cell} for municipality code {code} no "
            f"longer references the external [4]Abstracts workbook: "
            f"{formula!r}"
        )
