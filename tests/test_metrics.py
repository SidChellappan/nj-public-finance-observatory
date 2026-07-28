from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd
import pytest

from njpfo.build import REPRODUCIBLE_ARTIFACTS, build_all
from njpfo.build import build_latest_valid_table
from njpfo.normalize import apply_publication_rules
from njpfo.validate import (
    build_anomaly_ledger,
    collect_findings,
    percentage_scale_changes,
)


def test_per_capita_mismatch_is_warned_and_not_repaired(
    panel: pd.DataFrame,
) -> None:
    findings = collect_findings(panel)
    matches = [
        finding
        for finding in findings
        if finding.code == "per_capita_mismatch"
        and finding.municipality_code == "1114"
        and finding.budget_year == 2020
    ]
    assert matches
    row = panel[
        (panel["municipality_code"] == "1114")
        & (panel["budget_year"] == 2020)
    ].iloc[0]
    assert row["per_capita_net_debt"] > 7000
    assert row["calculated_per_capita_net_debt"] < 4000


def test_percentage_scale_change_detection_catches_100x() -> None:
    synthetic = pd.DataFrame(
        {
            "municipality_code": ["9999", "9999", "9999"],
            "budget_year": [2023, 2024, 2025],
            "example_pct": [1.0, 100.0, 1.1],
        }
    )
    findings = percentage_scale_changes(synthetic, "example_pct")
    assert len(findings) == 2
    assert all(finding.code == "percentage_scale_change" for finding in findings)


def test_tax_scale_break_is_logged_and_cannot_reach_latest_table(
    panel: pd.DataFrame,
) -> None:
    synthetic = panel.copy()
    selector = (
        (synthetic["municipality_code"] == "1103")
        & (synthetic["budget_year"] == 2025)
    )
    synthetic.loc[selector, "tax_collection_pct"] = 0.999917
    guarded = apply_publication_rules(synthetic)
    row = guarded.loc[selector].iloc[0]
    assert not bool(row["publication_eligible_tax_collection"])
    assert "50x" in row["tax_collection_publication_exclusion_reason"]

    latest = build_latest_valid_table(guarded)
    hamilton = latest[latest["municipality_code"] == "1103"].iloc[0]
    assert hamilton["tax_collection_budget_year"] == 2024

    ledger = build_anomaly_ledger(guarded)
    entry = ledger[
        (ledger["municipality_code"] == "1103")
        & (ledger["budget_year"] == 2025)
        & (ledger["field"] == "tax_collection_pct")
        & ledger["issue"].str.contains("scale", case=False)
    ]
    assert len(entry) == 1
    assert entry["publication_status"].str.contains("excluded").all()


def test_2024_valuation_anomaly_is_detected_for_all_targets(
    panel: pd.DataFrame,
) -> None:
    ledger = build_anomaly_ledger(panel)
    valuation = ledger[
        (ledger["budget_year"] == 2024)
        & (ledger["field"] == "three_year_average_property_valuation")
    ]
    assert set(valuation["municipality_code"]) == {
        "1103",
        "1107",
        "1111",
        "1113",
        "1114",
    }
    assert valuation["publication_status"].str.contains("excluded").all()
    assert valuation["explanatory_note"].str.contains(
        "external-workbook", regex=False
    ).all()


def test_princeton_2022_zero_is_retained_but_not_published(
    panel: pd.DataFrame,
) -> None:
    row = panel[
        (panel["municipality_code"] == "1114")
        & (panel["budget_year"] == 2022)
    ].iloc[0]
    assert row["net_debt"] == 0
    assert row["net_debt_source_value"] == "0"
    assert not bool(row["publication_eligible_net_debt"])
    assert "isolated" in row["net_debt_publication_exclusion_reason"]


def test_structural_imbalance_coverage_is_documented(panel: pd.DataFrame) -> None:
    assert panel["total_structural_imbalances"].notna().sum() == 50


def test_explicit_audit_field_no_data_values_are_in_ledger(
    panel: pd.DataFrame,
) -> None:
    ledger = build_anomaly_ledger(panel)
    for field in (
        "three_year_average_property_valuation",
        "net_debt_to_valuation_pct",
    ):
        source_missing = panel[
            panel[f"{field}_source_value"].str.casefold() == "no data"
        ][["municipality_code", "budget_year"]]
        logged = ledger[
            (ledger["field"] == field)
            & (ledger["source_value"].str.casefold() == "no data")
        ][["municipality_code", "budget_year"]]
        assert set(map(tuple, source_missing.to_numpy())) == set(
            map(tuple, logged.to_numpy())
        )


@pytest.mark.parametrize(
    ("municipality_code", "budget_year"),
    [("1103", 2020), ("1107", 2023)],
)
def test_tax_only_no_data_status_does_not_exclude_net_debt(
    panel: pd.DataFrame,
    municipality_code: str,
    budget_year: int,
) -> None:
    selector = (
        (panel["municipality_code"] == municipality_code)
        & (panel["budget_year"] == budget_year)
    )
    row = panel.loc[selector].iloc[0]
    assert bool(row["publication_eligible_net_debt"])
    assert not bool(row["publication_eligible_tax_collection"])

    ledger = build_anomaly_ledger(panel)
    entry = ledger[
        (ledger["municipality_code"] == municipality_code)
        & (ledger["budget_year"] == budget_year)
        & (ledger["field"] == "tax_collection_pct")
        & (ledger["source_value"].str.casefold() == "no data")
    ].iloc[0]
    assert entry["publication_status"] == (
        "included as null in downloadable audit panel; excluded from "
        "latest-valid tax selection"
    )
    assert "net-debt chart" not in entry["publication_status"]
    assert "debt selection" not in entry["publication_status"]


def test_audit_field_statuses_preserve_downloadable_panel_wording(
    panel: pd.DataFrame,
) -> None:
    ledger = build_anomaly_ledger(panel)
    audit_fields = {
        "population_estimate",
        "per_capita_net_debt",
        "total_structural_imbalances",
        "three_year_average_property_valuation",
        "net_debt_to_valuation_pct",
    }
    audit_entries = ledger[ledger["field"].isin(audit_fields)]
    assert not audit_entries.empty
    assert audit_entries["publication_status"].str.contains(
        "included in downloadable audit panel",
        regex=False,
    ).all()
    assert audit_entries["publication_status"].str.contains(
        "excluded from charts, latest-valid table, and interpretive claims",
        regex=False,
    ).all()
    assert not audit_entries["publication_status"].str.contains(
        "not published",
        case=False,
    ).any()


class _LocalAssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []
        self.chart_alts: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.references.append(values["href"] or "")
        if tag in {"img", "script", "link"}:
            attribute = "src" if tag in {"img", "script"} else "href"
            if values.get(attribute):
                self.references.append(values[attribute] or "")
        if tag == "img" and values.get("src", "").endswith(
            "net_debt_trend.svg"
        ):
            self.chart_alts.append(values.get("alt", "") or "")


def test_public_pages_have_working_local_links_and_accessibility_text(
    project_root: Path,
) -> None:
    docs = project_root / "docs"
    for name in ("index.html", "methods.html"):
        path = docs / name
        text = path.read_text(encoding="utf-8")
        assert "{{" not in text
        assert "These figures come from self-reported public budget records" in text
        parser = _LocalAssetParser()
        parser.feed(text)
        for reference in parser.references:
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc or reference.startswith("#"):
                continue
            local_path = (path.parent / parsed.path).resolve()
            assert local_path.exists(), f"Broken local reference: {name} -> {reference}"
        if name == "index.html":
            assert parser.chart_alts
            assert all(len(alt) > 80 for alt in parser.chart_alts)

    svg = (docs / "assets" / "net_debt_trend.svg").read_text(encoding="utf-8")
    assert '<title id="chart-title">' in svg
    assert '<desc id="chart-desc">' in svg
    assert 'role="img"' in svg


def test_clean_source_rebuild_reproduces_every_public_artifact(
    project_root: Path,
    tmp_path: Path,
) -> None:
    build_all(output_root=tmp_path, project_root=project_root)
    for relative in REPRODUCIBLE_ARTIFACTS:
        expected = project_root / relative
        rebuilt = tmp_path / relative
        assert rebuilt.is_file(), f"Rebuild did not create {relative}"
        assert rebuilt.read_bytes() == expected.read_bytes(), (
            f"Rebuild differs from committed artifact: {relative}"
        )
