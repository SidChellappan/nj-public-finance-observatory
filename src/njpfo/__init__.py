"""NJ Public Finance Observatory data pipeline."""

from pathlib import Path

__version__ = "0.1.0"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TARGET_MUNICIPALITIES = {
    "1103": "Hamilton",
    "1107": "Lawrence",
    "1111": "Trenton",
    "1113": "West Windsor",
    "1114": "Princeton",
}
TARGET_YEARS = tuple(range(2015, 2026))

SOURCE_PAGE_URL = "https://www.nj.gov/dca/dlgs/programs/mc_budgets.shtml"
SOURCE_WORKBOOK_URL = (
    "https://www.nj.gov/dca/dlgs/programs/mc_budget_docs/"
    "UFB%20Database%20-%20FINAL.xlsm"
)
SOURCE_WORKBOOK_NAME = "UFB Database - FINAL.xlsm"
SOURCE_RETRIEVAL_DATE = "2026-07-27"
SOURCE_SHA256 = "79a59be4c4ab2669d60ebb8072aab5a5775df7025e66cb95a887e1c39ed8ccaa"
SOURCE_SIZE_BYTES = 22_644_255

RAW_WORKBOOK = PROJECT_ROOT / "data" / "raw" / SOURCE_WORKBOOK_NAME
