"""Normalize raw workbook values without repairing suspicious observations."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from . import TARGET_MUNICIPALITIES

NO_DATA_TOKEN = "no data"

PANEL_COLUMNS = [
    "municipality_code",
    "municipality_name",
    "source_municipality_name",
    "budget_year",
    "population_estimate",
    "population_source_label",
    "net_debt",
    "per_capita_net_debt",
    "calculated_per_capita_net_debt",
    "tax_collection_pct",
    "tax_collection_reference_year",
    "no_ufb_available",
    "significant_data_missing",
    "missingness_reason",
    "total_structural_imbalances",
    "three_year_average_property_valuation",
    "net_debt_to_valuation_pct",
    "publication_eligible_net_debt",
    "net_debt_publication_exclusion_reason",
    "publication_eligible_tax_collection",
    "tax_collection_publication_exclusion_reason",
    "source_workbook",
    "source_sheet",
    "source_row",
    "population_estimate_source_cell",
    "net_debt_source_cell",
    "per_capita_net_debt_source_cell",
    "tax_collection_pct_source_cell",
    "no_ufb_available_source_cell",
    "significant_data_missing_source_cell",
    "total_structural_imbalances_source_cell",
    "three_year_average_property_valuation_source_cell",
    "net_debt_to_valuation_pct_source_cell",
    "population_estimate_source_value",
    "net_debt_source_value",
    "per_capita_net_debt_source_value",
    "tax_collection_pct_source_value",
    "no_ufb_available_source_value",
    "significant_data_missing_source_value",
    "total_structural_imbalances_source_value",
    "three_year_average_property_valuation_source_value",
    "net_debt_to_valuation_pct_source_value",
]


def is_no_data(value: Any) -> bool:
    return isinstance(value, str) and value.strip().casefold() == NO_DATA_TOKEN


def source_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return format(value, ".15g")
    return str(value).strip()


def normalize_number(value: Any) -> float | None:
    if value is None or value == "" or is_no_data(value):
        return None
    if isinstance(value, bool):
        raise ValueError(f"Boolean is not a numeric source value: {value!r}")
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "").replace("$", "")
    if not text:
        return None
    return float(text)


def normalize_flag(value: Any) -> bool:
    if value is None or str(value).strip() == "":
        return False
    if str(value).strip().casefold() in {"x", "yes", "true", "1"}:
        return True
    raise ValueError(f"Unrecognized source flag: {value!r}")


def _rounded(value: float | None, digits: int) -> float | None:
    return None if value is None else round(value, digits)


def _flag_exclusion_reason(no_ufb: bool, significant_missing: bool) -> str:
    reasons: list[str] = []
    if no_ufb:
        reasons.append("source marks No UFB Available")
    if significant_missing:
        reasons.append("source marks Significant Data Missing")
    return "; ".join(reasons)


def _append_reason(existing: Any, reason: str) -> str:
    existing_text = "" if pd.isna(existing) else str(existing)
    parts = [
        part.strip()
        for part in existing_text.split(";")
        if part.strip()
    ]
    if reason not in parts:
        parts.append(reason)
    return "; ".join(parts)


def apply_publication_rules(panel: pd.DataFrame) -> pd.DataFrame:
    """Apply field-specific safety rules without changing source values."""

    result = panel.copy()
    for _, group in result.groupby("municipality_code", sort=False):
        ordered = group.sort_values("budget_year")
        indices = list(ordered.index)
        for position in range(1, len(indices) - 1):
            current = indices[position]
            previous = indices[position - 1]
            following = indices[position + 1]
            if (
                result.at[current, "net_debt"] == 0
                and result.at[previous, "net_debt"] > 0
                and result.at[following, "net_debt"] > 0
            ):
                result.at[current, "publication_eligible_net_debt"] = False
                result.at[
                    current, "net_debt_publication_exclusion_reason"
                ] = _append_reason(
                    result.at[
                        current, "net_debt_publication_exclusion_reason"
                    ],
                    "reported zero is isolated between positive adjacent "
                    "years and remains unreconciled",
                )

        valid_tax = [
            index
            for index in indices
            if pd.notna(result.at[index, "tax_collection_pct"])
            and result.at[index, "tax_collection_pct"] > 0
        ]
        for previous, current in zip(valid_tax, valid_tax[1:], strict=False):
            if (
                result.at[current, "budget_year"]
                - result.at[previous, "budget_year"]
                != 1
            ):
                continue
            previous_value = result.at[previous, "tax_collection_pct"]
            current_value = result.at[current, "tax_collection_pct"]
            factor = max(previous_value, current_value) / min(
                previous_value, current_value
            )
            if factor >= 50:
                lower = (
                    previous
                    if previous_value < current_value
                    else current
                )
                result.at[
                    lower, "publication_eligible_tax_collection"
                ] = False
                result.at[
                    lower, "tax_collection_publication_exclusion_reason"
                ] = _append_reason(
                    result.at[
                        lower,
                        "tax_collection_publication_exclusion_reason",
                    ],
                    "tax-collection percentage differs in scale by at least "
                    "50x from an adjacent year",
                )
    return result


def normalize_records(records: Iterable[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    numeric_fields = (
        "population_estimate",
        "net_debt",
        "per_capita_net_debt",
        "tax_collection_pct",
        "total_structural_imbalances",
        "three_year_average_property_valuation",
        "net_debt_to_valuation_pct",
    )
    raw_fields = (
        *numeric_fields,
        "no_ufb_available",
        "significant_data_missing",
    )

    for raw in records:
        code = raw["municipality_code"]
        values = {field: normalize_number(raw.get(field)) for field in numeric_fields}
        no_ufb = normalize_flag(raw.get("no_ufb_available"))
        significant_missing = normalize_flag(raw.get("significant_data_missing"))
        missing_fields = [
            field for field in numeric_fields if is_no_data(raw.get(field))
        ]

        missing_reasons: list[str] = []
        if no_ufb:
            missing_reasons.append(
                "NJ DCA marks No UFB Available (no User-Friendly Budget on file)."
            )
        if significant_missing:
            missing_reasons.append(
                "NJ DCA marks Significant Data Missing "
                "(at least one entire section was blank)."
            )
        if missing_fields:
            missing_reasons.append(
                "Source reports No data for: " + ", ".join(missing_fields) + "."
            )

        calculated_per_capita = None
        population = values["population_estimate"]
        net_debt = values["net_debt"]
        if (
            population is not None
            and population > 0
            and net_debt is not None
        ):
            calculated_per_capita = net_debt / population

        common_exclusion = _flag_exclusion_reason(no_ufb, significant_missing)
        debt_reasons = [common_exclusion] if common_exclusion else []
        tax_reasons = [common_exclusion] if common_exclusion else []
        if values["net_debt"] is None:
            debt_reasons.append("reported net debt is unavailable")
        if values["tax_collection_pct"] is None:
            tax_reasons.append("reported tax-collection percentage is unavailable")

        row: dict[str, Any] = {
            "municipality_code": code,
            "municipality_name": TARGET_MUNICIPALITIES[code],
            "source_municipality_name": source_text(
                raw.get("source_municipality_name")
            ),
            "budget_year": int(raw["budget_year"]),
            "population_estimate": (
                None
                if population is None
                else int(population)
                if population.is_integer()
                else round(population, 6)
            ),
            "population_source_label": raw["population_source_label"],
            "net_debt": _rounded(net_debt, 2),
            "per_capita_net_debt": _rounded(
                values["per_capita_net_debt"], 6
            ),
            "calculated_per_capita_net_debt": _rounded(
                calculated_per_capita, 6
            ),
            # The workbook stores percent-formatted cells as fractions.
            "tax_collection_pct": _rounded(
                None
                if values["tax_collection_pct"] is None
                else values["tax_collection_pct"] * 100,
                6,
            ),
            "tax_collection_reference_year": int(
                raw["tax_collection_reference_year"]
            ),
            "no_ufb_available": no_ufb,
            "significant_data_missing": significant_missing,
            "missingness_reason": " ".join(missing_reasons),
            "total_structural_imbalances": _rounded(
                values["total_structural_imbalances"], 2
            ),
            "three_year_average_property_valuation": _rounded(
                values["three_year_average_property_valuation"], 2
            ),
            "net_debt_to_valuation_pct": _rounded(
                None
                if values["net_debt_to_valuation_pct"] is None
                else values["net_debt_to_valuation_pct"] * 100,
                6,
            ),
            "publication_eligible_net_debt": not debt_reasons,
            "net_debt_publication_exclusion_reason": "; ".join(debt_reasons),
            "publication_eligible_tax_collection": not tax_reasons,
            "tax_collection_publication_exclusion_reason": "; ".join(
                tax_reasons
            ),
            "source_workbook": raw["source_workbook"],
            "source_sheet": raw["source_sheet"],
            "source_row": int(raw["source_row"]),
        }
        for field in raw_fields:
            row[f"{field}_source_cell"] = raw[f"{field}_source_cell"]
            row[f"{field}_source_value"] = source_text(raw.get(field))
        rows.append(row)

    panel = pd.DataFrame(rows)
    panel = panel.sort_values(
        ["municipality_code", "budget_year"], kind="stable"
    ).reset_index(drop=True)

    # Suspicious values remain in the panel exactly as reported. Publication
    # rules only control whether those values can reach the chart or table.
    panel = apply_publication_rules(panel)
    return panel[PANEL_COLUMNS]
