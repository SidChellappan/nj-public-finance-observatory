from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def panel(project_root: Path) -> pd.DataFrame:
    return pd.read_csv(
        project_root / "data" / "processed" / "mercer_fiscal_panel.csv",
        dtype={"municipality_code": str},
    )
