from __future__ import annotations

import pandas as pd

from njpfo import TARGET_MUNICIPALITIES, TARGET_YEARS
from njpfo.build import build_latest_valid_table
from njpfo.chart import publication_chart_data


def test_panel_is_exact_target_cross_product(panel: pd.DataFrame) -> None:
    actual = set(
        zip(
            panel["municipality_code"],
            panel["budget_year"],
            strict=False,
        )
    )
    expected = {
        (code, year)
        for code in TARGET_MUNICIPALITIES
        for year in TARGET_YEARS
    }
    assert len(panel) == 55
    assert actual == expected


def test_display_names_are_mapped_from_codes(panel: pd.DataFrame) -> None:
    for code, name in TARGET_MUNICIPALITIES.items():
        assert set(
            panel.loc[panel["municipality_code"] == code, "municipality_name"]
        ) == {name}
    assert set(
        panel.loc[panel["municipality_code"] == "1114", "source_municipality_name"]
    ) == {"Princeton borough"}


def test_trenton_2025_missing_debt_row_is_preserved(panel: pd.DataFrame) -> None:
    row = panel[
        (panel["municipality_code"] == "1111")
        & (panel["budget_year"] == 2025)
    ].iloc[0]
    assert pd.isna(row["net_debt"])
    assert row["net_debt_source_value"] == "No data"
    assert not bool(row["publication_eligible_net_debt"])
    assert row["source_sheet"] == "2025 Summary"
    assert row["net_debt_source_cell"].startswith("LT")


def test_chart_data_never_publishes_flagged_or_missing_rows(
    panel: pd.DataFrame,
) -> None:
    chart = publication_chart_data(panel)
    source_flag = chart["no_ufb_available"] | chart["significant_data_missing"]
    assert chart.loc[source_flag, "net_debt"].isna().all()
    ineligible = ~chart["publication_eligible_net_debt"]
    assert chart.loc[ineligible, "net_debt"].isna().all()
    assert chart.loc[chart["publication_eligible_net_debt"], "net_debt"].notna().all()


def test_latest_valid_table_is_field_specific_and_traceable(
    panel: pd.DataFrame,
) -> None:
    latest = build_latest_valid_table(panel)
    assert list(latest["municipality_code"]) == list(TARGET_MUNICIPALITIES)
    assert len(latest) == 5

    trenton = latest[latest["municipality_code"] == "1111"].iloc[0]
    assert trenton["net_debt_budget_year"] == 2024
    assert trenton["tax_collection_budget_year"] == 2024
    assert trenton["tax_collection_reference_year"] == 2023

    other = latest[latest["municipality_code"] != "1111"]
    assert set(other["net_debt_budget_year"]) == {2025}
    assert set(other["tax_collection_budget_year"]) == {2025}
    assert latest["net_debt_source_cell"].str.match(r"^[A-Z]+\d+$").all()
    assert latest["tax_collection_source_cell"].str.match(r"^[A-Z]+\d+$").all()


def test_source_layout_shift_is_traceable(panel: pd.DataFrame) -> None:
    earlier = panel[panel["budget_year"] == 2024]
    latest = panel[panel["budget_year"] == 2025]
    assert earlier["net_debt_source_cell"].str.startswith("LU").all()
    assert latest["net_debt_source_cell"].str.startswith("LT").all()
    assert earlier["total_structural_imbalances_source_cell"].str.startswith(
        "OQ"
    ).all()
    assert latest["total_structural_imbalances_source_cell"].str.startswith(
        "OP"
    ).all()
