"""Contract validation and anomaly-ledger construction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from . import TARGET_MUNICIPALITIES, TARGET_YEARS

EXPECTED_ROW_COUNT = len(TARGET_MUNICIPALITIES) * len(TARGET_YEARS)
PER_CAPITA_RELATIVE_TOLERANCE = 0.05

ANOMALY_COLUMNS = [
    "municipality_code",
    "municipality_name",
    "budget_year",
    "field",
    "source_value",
    "issue",
    "treatment",
    "publication_status",
    "explanatory_note",
    "source_sheet",
    "source_cell",
]


class DataContractError(RuntimeError):
    """Raised when a serious data-contract violation blocks the build."""


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    municipality_code: str = ""
    budget_year: int | None = None
    field: str = ""


def _error(code: str, message: str, **context: Any) -> Finding:
    return Finding("error", code, message, **context)


def _warning(code: str, message: str, **context: Any) -> Finding:
    return Finding("warning", code, message, **context)


def percentage_scale_changes(
    panel: pd.DataFrame,
    column: str,
    *,
    factor_threshold: float = 50.0,
) -> list[Finding]:
    findings: list[Finding] = []
    for code, group in panel.groupby("municipality_code", sort=False):
        ordered = group.sort_values("budget_year")
        previous_value: float | None = None
        previous_year: int | None = None
        for row in ordered.itertuples(index=False):
            value = getattr(row, column)
            if pd.isna(value) or value <= 0:
                continue
            if previous_value is not None and previous_value > 0:
                factor = max(value, previous_value) / min(value, previous_value)
                if factor >= factor_threshold:
                    findings.append(
                        _warning(
                            "percentage_scale_change",
                            f"{column} changes by {factor:.1f}x between "
                            f"{previous_year} and {row.budget_year}.",
                            municipality_code=str(code),
                            budget_year=int(row.budget_year),
                            field=column,
                        )
                    )
            previous_value = float(value)
            previous_year = int(row.budget_year)
    return findings


def collect_findings(panel: pd.DataFrame) -> list[Finding]:
    findings: list[Finding] = []
    keys = ["municipality_code", "budget_year"]

    duplicates = panel[panel.duplicated(keys, keep=False)]
    if not duplicates.empty:
        findings.append(
            _error(
                "duplicate_key",
                "Duplicate municipality-year keys: "
                + ", ".join(
                    f"{row.municipality_code}/{row.budget_year}"
                    for row in duplicates.itertuples(index=False)
                ),
            )
        )

    if len(panel) != EXPECTED_ROW_COUNT:
        findings.append(
            _error(
                "row_count",
                f"Expected {EXPECTED_ROW_COUNT} panel rows; found {len(panel)}.",
            )
        )

    actual_codes = set(panel["municipality_code"].astype(str))
    missing_codes = set(TARGET_MUNICIPALITIES) - actual_codes
    if missing_codes:
        findings.append(
            _error(
                "missing_target_codes",
                f"Missing target municipality codes: {sorted(missing_codes)}.",
            )
        )

    invalid_years = sorted(set(panel["budget_year"]) - set(TARGET_YEARS))
    if invalid_years:
        findings.append(
            _error(
                "invalid_year",
                f"Years outside 2015-2025: {invalid_years}.",
            )
        )

    expected_keys = {
        (code, year)
        for code in TARGET_MUNICIPALITIES
        for year in TARGET_YEARS
    }
    actual_keys = set(
        zip(
            panel["municipality_code"].astype(str),
            panel["budget_year"].astype(int),
            strict=False,
        )
    )
    missing_keys = sorted(expected_keys - actual_keys)
    if missing_keys:
        findings.append(
            _error(
                "missing_panel_rows",
                "Normalization lost municipality-year rows: "
                + ", ".join(f"{code}/{year}" for code, year in missing_keys),
            )
        )

    for field in ("population_estimate", "net_debt"):
        invalid = panel[panel[field].notna() & (panel[field] < 0)]
        for row in invalid.itertuples(index=False):
            findings.append(
                _error(
                    "negative_value",
                    f"{field} is negative.",
                    municipality_code=row.municipality_code,
                    budget_year=int(row.budget_year),
                    field=field,
                )
            )

    source_pairs = {
        "population_estimate": "population_estimate_source_value",
        "net_debt": "net_debt_source_value",
        "per_capita_net_debt": "per_capita_net_debt_source_value",
        "tax_collection_pct": "tax_collection_pct_source_value",
        "total_structural_imbalances": (
            "total_structural_imbalances_source_value"
        ),
    }
    for normalized, source in source_pairs.items():
        source_is_no_data = (
            panel[source].fillna("").astype(str).str.strip().str.casefold()
            == "no data"
        )
        corrupted = panel[source_is_no_data & panel[normalized].notna()]
        for row in corrupted.itertuples(index=False):
            findings.append(
                _error(
                    "no_data_became_number",
                    f"{normalized} has a numeric value although its source "
                    "representation is 'No data'.",
                    municipality_code=row.municipality_code,
                    budget_year=int(row.budget_year),
                    field=normalized,
                )
            )

    invalid_tax = panel[
        panel["tax_collection_pct"].notna()
        & ~panel["tax_collection_pct"].between(0, 100)
    ]
    for row in invalid_tax.itertuples(index=False):
        findings.append(
            _error(
                "invalid_percentage",
                "tax_collection_pct is outside 0-100 percentage points.",
                municipality_code=row.municipality_code,
                budget_year=int(row.budget_year),
                field="tax_collection_pct",
            )
        )

    comparable = panel[
        panel["net_debt"].notna()
        & panel["per_capita_net_debt"].notna()
        & panel["population_estimate"].notna()
        & (panel["net_debt"] > 0)
        & (panel["population_estimate"] > 0)
    ]
    for row in comparable.itertuples(index=False):
        calculated = row.net_debt / row.population_estimate
        relative_error = abs(row.per_capita_net_debt - calculated) / calculated
        if relative_error > PER_CAPITA_RELATIVE_TOLERANCE:
            findings.append(
                _warning(
                    "per_capita_mismatch",
                    "Reported per-capita net debt differs from reported net "
                    f"debt divided by population by {relative_error:.1%}.",
                    municipality_code=row.municipality_code,
                    budget_year=int(row.budget_year),
                    field="per_capita_net_debt",
                )
            )

    findings.extend(
        percentage_scale_changes(panel, "net_debt_to_valuation_pct")
    )
    findings.extend(percentage_scale_changes(panel, "tax_collection_pct"))

    source_flag = panel["no_ufb_available"] | panel["significant_data_missing"]
    for eligibility, value_field in (
        ("publication_eligible_net_debt", "net_debt"),
        ("publication_eligible_tax_collection", "tax_collection_pct"),
    ):
        bad = panel[panel[eligibility] & source_flag]
        for row in bad.itertuples(index=False):
            findings.append(
                _error(
                    "flagged_value_published",
                    f"{value_field} is marked publication-eligible despite "
                    "a source missing-data flag.",
                    municipality_code=row.municipality_code,
                    budget_year=int(row.budget_year),
                    field=value_field,
                )
            )
        missing = panel[panel[eligibility] & panel[value_field].isna()]
        for row in missing.itertuples(index=False):
            findings.append(
                _error(
                    "missing_value_published",
                    f"{value_field} is marked publication-eligible but is null.",
                    municipality_code=row.municipality_code,
                    budget_year=int(row.budget_year),
                    field=value_field,
                )
            )

    return findings


def validate_panel(panel: pd.DataFrame) -> list[Finding]:
    findings = collect_findings(panel)
    errors = [finding for finding in findings if finding.severity == "error"]
    if errors:
        details = "\n".join(
            f"- [{finding.code}] {finding.message}" for finding in errors
        )
        raise DataContractError(f"Data contract failed:\n{details}")
    return [finding for finding in findings if finding.severity == "warning"]


def _ledger_row(
    row: Any,
    *,
    field: str,
    source_value: str,
    issue: str,
    treatment: str,
    publication_status: str,
    note: str,
    source_cell: str,
) -> dict[str, Any]:
    return {
        "municipality_code": row.municipality_code,
        "municipality_name": row.municipality_name,
        "budget_year": int(row.budget_year),
        "field": field,
        "source_value": source_value,
        "issue": issue,
        "treatment": treatment,
        "publication_status": publication_status,
        "explanatory_note": note,
        "source_sheet": row.source_sheet,
        "source_cell": source_cell,
    }


AUDIT_FIELD_PUBLICATION_STATUS = (
    "included in downloadable audit panel; excluded from charts, "
    "latest-valid table, and interpretive claims"
)

MISSING_VALUE_PUBLICATION_STATUSES = {
    "net_debt": (
        "included as null in downloadable audit panel; excluded from "
        "net-debt chart and latest-valid debt selection"
    ),
    "tax_collection_pct": (
        "included as null in downloadable audit panel; excluded from "
        "latest-valid tax selection"
    ),
}


def build_anomaly_ledger(panel: pd.DataFrame) -> pd.DataFrame:
    ledger: list[dict[str, Any]] = []
    for row in panel.itertuples(index=False):
        if row.no_ufb_available:
            ledger.append(
                _ledger_row(
                    row,
                    field="no_ufb_available",
                    source_value=row.no_ufb_available_source_value,
                    issue="NJ DCA marks No UFB Available.",
                    treatment="Row retained; source values normalized without imputation.",
                    publication_status=(
                        "included as source flag in downloadable audit panel; "
                        "row excluded from net-debt chart and latest-valid "
                        "debt and tax selections"
                    ),
                    note=(
                        "The source glossary says NJ DCA does not have a "
                        "User-Friendly Budget on file for this municipality."
                    ),
                    source_cell=row.no_ufb_available_source_cell,
                )
            )
        if row.significant_data_missing:
            ledger.append(
                _ledger_row(
                    row,
                    field="significant_data_missing",
                    source_value=row.significant_data_missing_source_value,
                    issue="NJ DCA marks Significant Data Missing.",
                    treatment="Row retained; source values normalized without imputation.",
                    publication_status=(
                        "included as source flag in downloadable audit panel; "
                        "row excluded from net-debt chart and latest-valid "
                        "debt and tax selections"
                    ),
                    note=(
                        "The source glossary says at least one entire UFB "
                        "section was left blank."
                    ),
                    source_cell=row.significant_data_missing_source_cell,
                )
            )

        missing_fields = (
            ("population_estimate", "population_estimate_source_value"),
            ("net_debt", "net_debt_source_value"),
            ("per_capita_net_debt", "per_capita_net_debt_source_value"),
            ("tax_collection_pct", "tax_collection_pct_source_value"),
            (
                "total_structural_imbalances",
                "total_structural_imbalances_source_value",
            ),
            (
                "three_year_average_property_valuation",
                "three_year_average_property_valuation_source_value",
            ),
            (
                "net_debt_to_valuation_pct",
                "net_debt_to_valuation_pct_source_value",
            ),
        )
        for field, source_field in missing_fields:
            if pd.isna(getattr(row, field)) and getattr(row, source_field).casefold() == "no data":
                ledger.append(
                    _ledger_row(
                        row,
                        field=field,
                        source_value=getattr(row, source_field),
                        issue="Source explicitly reports 'No data'.",
                        treatment="Normalized to null; row retained; no imputation.",
                        publication_status=MISSING_VALUE_PUBLICATION_STATUSES.get(
                            field,
                            "included in downloadable audit panel as null; "
                            "excluded from charts, latest-valid table, and "
                            "interpretive claims",
                        ),
                        note=(
                            "Textual missingness is preserved as null and "
                            "never converted to numeric zero."
                        ),
                        source_cell=getattr(row, f"{field}_source_cell"),
                    )
                )

        if (
            pd.notna(row.net_debt)
            and row.net_debt > 0
            and pd.notna(row.per_capita_net_debt)
            and pd.notna(row.population_estimate)
            and row.population_estimate > 0
        ):
            calculated = row.net_debt / row.population_estimate
            relative_error = abs(row.per_capita_net_debt - calculated) / calculated
            if relative_error > PER_CAPITA_RELATIVE_TOLERANCE:
                ledger.append(
                    _ledger_row(
                        row,
                        field="per_capita_net_debt",
                        source_value=row.per_capita_net_debt_source_value,
                        issue=(
                            "Reported per-capita value differs from net debt "
                            f"divided by population by {relative_error:.1%}."
                        ),
                        treatment=(
                            "Reported value retained; calculated comparison "
                            "stored separately; no correction made."
                        ),
                        publication_status=AUDIT_FIELD_PUBLICATION_STATUS,
                        note=(
                            f"Calculated comparison is ${calculated:,.2f} "
                            "per resident using this row's reported values."
                        ),
                        source_cell=row.per_capita_net_debt_source_cell,
                    )
                )

    scale_entries: set[tuple[str, int, str]] = set()
    for code, group in panel.groupby("municipality_code", sort=False):
        ordered = group.sort_values("budget_year")
        valid = ordered[
            ordered["tax_collection_pct"].notna()
            & (ordered["tax_collection_pct"] > 0)
        ]
        rows = list(valid.itertuples(index=False))
        for previous, current in zip(rows, rows[1:], strict=False):
            if current.budget_year - previous.budget_year != 1:
                continue
            factor = max(
                previous.tax_collection_pct,
                current.tax_collection_pct,
            ) / min(
                previous.tax_collection_pct,
                current.tax_collection_pct,
            )
            if factor < 50:
                continue
            lower = (
                previous
                if previous.tax_collection_pct
                < current.tax_collection_pct
                else current
            )
            key = (code, int(lower.budget_year), "tax_collection_pct")
            if key in scale_entries:
                continue
            scale_entries.add(key)
            ledger.append(
                _ledger_row(
                    lower,
                    field="tax_collection_pct",
                    source_value=lower.tax_collection_pct_source_value,
                    issue=(
                        "Normalized percentage differs in scale from an "
                        f"adjacent year by {factor:.1f}x."
                    ),
                    treatment=(
                        "Source value retained; excluded from latest-valid "
                        "selection pending scale review."
                    ),
                    publication_status=(
                        "included in downloadable audit panel; excluded from "
                        "latest-valid tax selection pending scale review"
                    ),
                    note=(
                        "The lower of the two adjacent percentage values is "
                        "treated as the likely scale break; no value is repaired."
                    ),
                    source_cell=lower.tax_collection_pct_source_cell,
                )
            )

    for code, group in panel.groupby("municipality_code", sort=False):
        indexed = group.set_index("budget_year")
        if {2023, 2024, 2025}.issubset(indexed.index):
            prior = indexed.at[2023, "three_year_average_property_valuation"]
            current = indexed.at[2024, "three_year_average_property_valuation"]
            following = indexed.at[2025, "three_year_average_property_valuation"]
            if (
                pd.notna(prior)
                and pd.notna(current)
                and pd.notna(following)
                and current < min(prior, following) / 10
            ):
                row = indexed.loc[2024]
                factor = min(prior, following) / current
                ledger.append(
                    {
                        "municipality_code": code,
                        "municipality_name": row["municipality_name"],
                        "budget_year": 2024,
                        "field": "three_year_average_property_valuation",
                        "source_value": row[
                            "three_year_average_property_valuation_source_value"
                        ],
                        "issue": (
                            "2024 cached valuation is sharply below adjacent "
                            f"years (at least {factor:.1f}x scale difference)."
                        ),
                        "treatment": (
                            "Raw value retained for audit; valuation-derived "
                            "ratio excluded; reported net debt left unchanged."
                        ),
                        "publication_status": (
                            AUDIT_FIELD_PUBLICATION_STATUS
                        ),
                        "explanatory_note": (
                            "The 2024 workbook cell is an external-workbook "
                            "VLOOKUP and its cached value is unreconciled."
                        ),
                        "source_sheet": row["source_sheet"],
                        "source_cell": row[
                            "three_year_average_property_valuation_source_cell"
                        ],
                    }
                )

    for code, group in panel.groupby("municipality_code", sort=False):
        ordered = group.sort_values("budget_year").reset_index(drop=True)
        for position in range(1, len(ordered) - 1):
            row = ordered.iloc[position]
            if (
                row["net_debt"] == 0
                and ordered.iloc[position - 1]["net_debt"] > 0
                and ordered.iloc[position + 1]["net_debt"] > 0
            ):
                ledger.append(
                    {
                        "municipality_code": code,
                        "municipality_name": row["municipality_name"],
                        "budget_year": int(row["budget_year"]),
                        "field": "net_debt",
                        "source_value": row["net_debt_source_value"],
                        "issue": (
                            "Reported zero is isolated between positive "
                            "adjacent-year debt values."
                        ),
                        "treatment": (
                            "Source zero retained; not reclassified as missing; "
                            "excluded from the chart pending clarification."
                        ),
                        "publication_status": (
                            "included in downloadable audit panel; excluded "
                            "from net-debt chart and latest-valid debt "
                            "selection pending clarification"
                        ),
                        "explanatory_note": (
                            "All underlying net-debt components in the source "
                            "row are numeric zero, while adjacent years exceed "
                            "$90 million."
                        ),
                        "source_sheet": row["source_sheet"],
                        "source_cell": row["net_debt_source_cell"],
                    }
                )

    result = pd.DataFrame(ledger, columns=ANOMALY_COLUMNS)
    if result.empty:
        return result
    return result.sort_values(
        ["municipality_code", "budget_year", "field", "issue"],
        kind="stable",
    ).reset_index(drop=True)


def findings_as_records(findings: list[Finding]) -> list[dict[str, Any]]:
    return [asdict(finding) for finding in findings]
