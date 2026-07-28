from __future__ import annotations

import pandas as pd
import pytest

from njpfo.normalize import normalize_number
from njpfo.validate import DataContractError, validate_panel


def test_committed_panel_passes_serious_contract_checks(panel: pd.DataFrame) -> None:
    warnings = validate_panel(panel)
    assert warnings
    assert all(finding.severity == "warning" for finding in warnings)


def test_duplicate_municipality_year_key_fails(panel: pd.DataFrame) -> None:
    duplicate = pd.concat([panel, panel.iloc[[0]]], ignore_index=True)
    with pytest.raises(DataContractError, match="Duplicate municipality-year"):
        validate_panel(duplicate)


def test_missing_target_code_and_non_55_row_panel_fail(
    panel: pd.DataFrame,
) -> None:
    missing_target = panel[panel["municipality_code"] != "1103"].copy()
    with pytest.raises(DataContractError) as exc_info:
        validate_panel(missing_target)
    message = str(exc_info.value)
    assert "Expected 55 panel rows" in message
    assert "Missing target municipality codes" in message


def test_loss_of_one_missing_row_fails(panel: pd.DataFrame) -> None:
    lost = panel[
        ~(
            (panel["municipality_code"] == "1111")
            & (panel["budget_year"] == 2015)
        )
    ].copy()
    with pytest.raises(DataContractError, match="Normalization lost"):
        validate_panel(lost)


def test_invalid_year_fails(panel: pd.DataFrame) -> None:
    invalid = panel.copy()
    invalid.loc[0, "budget_year"] = 2014
    with pytest.raises(DataContractError, match="Years outside 2015-2025"):
        validate_panel(invalid)


@pytest.mark.parametrize("field", ["population_estimate", "net_debt"])
def test_negative_core_metric_fails(panel: pd.DataFrame, field: str) -> None:
    invalid = panel.copy()
    invalid.loc[0, field] = -1
    with pytest.raises(DataContractError, match=f"{field} is negative"):
        validate_panel(invalid)


def test_no_data_normalizes_to_null_not_zero(panel: pd.DataFrame) -> None:
    assert normalize_number("No data") is None
    corrupted = panel.copy()
    selector = (
        (corrupted["municipality_code"] == "1111")
        & (corrupted["budget_year"] == 2025)
    )
    assert corrupted.loc[selector, "net_debt_source_value"].iloc[0] == "No data"
    corrupted.loc[selector, "net_debt"] = 0
    with pytest.raises(DataContractError, match="No data"):
        validate_panel(corrupted)


def test_publication_eligible_source_flag_fails(panel: pd.DataFrame) -> None:
    corrupted = panel.copy()
    flagged = corrupted["significant_data_missing"].astype(bool)
    index = corrupted[flagged].index[0]
    corrupted.loc[index, "publication_eligible_net_debt"] = True
    with pytest.raises(DataContractError, match="missing-data flag"):
        validate_panel(corrupted)


def test_publication_eligible_null_fails(panel: pd.DataFrame) -> None:
    corrupted = panel.copy()
    index = corrupted[corrupted["publication_eligible_net_debt"]].index[0]
    corrupted.loc[index, "net_debt"] = float("nan")
    with pytest.raises(DataContractError, match="marked publication-eligible but is null"):
        validate_panel(corrupted)
