"""One-command deterministic build for data, chart, table, and public pages."""

from __future__ import annotations

import argparse
import html
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

from . import (
    PROJECT_ROOT,
    RAW_WORKBOOK,
    SOURCE_RETRIEVAL_DATE,
    SOURCE_PAGE_URL,
    SOURCE_SHA256,
    SOURCE_WORKBOOK_NAME,
    SOURCE_WORKBOOK_URL,
    TARGET_MUNICIPALITIES,
)
from .chart import build_chart
from .download import ensure_source
from .extract import extract_records
from .normalize import PANEL_COLUMNS, normalize_records
from .validate import (
    ANOMALY_COLUMNS,
    Finding,
    build_anomaly_ledger,
    validate_panel,
)

TEMPLATE_DIRECTORY = Path(__file__).with_name("templates")

REPRODUCIBLE_ARTIFACTS = (
    "data/processed/mercer_fiscal_panel.csv",
    "data/processed/latest_valid_indicators.csv",
    "data/data_dictionary.csv",
    "data/anomaly_ledger.csv",
    "docs/assets/net_debt_trend.svg",
    "docs/assets/site.css",
    "docs/index.html",
    "docs/methods.html",
    "docs/downloads/mercer_fiscal_panel.csv",
    "docs/downloads/data_dictionary.csv",
    "docs/downloads/anomaly_ledger.csv",
    "docs/downloads/njpfo-source.zip",
    "docs/.nojekyll",
)


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
        na_rep="",
    )


def build_latest_valid_table(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for code, name in TARGET_MUNICIPALITIES.items():
        municipal = panel[panel["municipality_code"] == code].sort_values(
            "budget_year"
        )
        debt = municipal[municipal["publication_eligible_net_debt"]].iloc[-1]
        tax = municipal[
            municipal["publication_eligible_tax_collection"]
        ].iloc[-1]
        rows.append(
            {
                "municipality_code": code,
                "municipality_name": name,
                "net_debt_budget_year": int(debt["budget_year"]),
                "net_debt": float(debt["net_debt"]),
                "net_debt_unit": "current dollars, as reported",
                "net_debt_source_sheet": debt["source_sheet"],
                "net_debt_source_cell": debt["net_debt_source_cell"],
                "tax_collection_budget_year": int(tax["budget_year"]),
                "tax_collection_reference_year": int(
                    tax["tax_collection_reference_year"]
                ),
                "tax_collection_pct": float(tax["tax_collection_pct"]),
                "tax_collection_unit": "percentage points",
                "tax_collection_source_sheet": tax["source_sheet"],
                "tax_collection_source_cell": tax[
                    "tax_collection_pct_source_cell"
                ],
            }
        )
    return pd.DataFrame(rows)


def build_data_dictionary() -> pd.DataFrame:
    specifications: dict[str, tuple[str, str, str, str, str]] = {
        "municipality_code": (
            "Stable four-digit municipality identifier used for every join.",
            "code",
            "Muni-code (column A)",
            "Left-pad numeric representations to four digits.",
            "Never missing for an accepted panel row.",
        ),
        "municipality_name": (
            "Plain-language display name assigned from the municipality code.",
            "text",
            "Project code-to-name lookup",
            "Map only after joining on municipality_code.",
            "Never missing for a target code.",
        ),
        "source_municipality_name": (
            "Municipality label exactly as distributed in the source sheet.",
            "text",
            "Municipality",
            "Trim surrounding whitespace; otherwise preserve.",
            "Retain source text even when the display name differs.",
        ),
        "budget_year": (
            "Year named by the annual Summary sheet.",
            "year",
            "Annual sheet name",
            "Parse the leading four-digit year from the sheet name.",
            "Must be one of 2015 through 2025.",
        ),
        "population_estimate": (
            "Population value reported on the annual Summary sheet.",
            "people",
            "Annual population column (I)",
            "Convert numeric source value; do not interpolate.",
            "'No data' becomes null, never zero.",
        ),
        "population_source_label": (
            "Full annual source header identifying the population vintage.",
            "text",
            "Summary sheet header row 5",
            "Preserve source header text.",
            "Never missing when the workbook contract passes.",
        ),
        "net_debt": (
            "Gross debt less deductions, as reported by NJ DCA.",
            "current dollars",
            "Net Debt",
            "Convert numeric source value and round to cents; no inflation adjustment.",
            "'No data' becomes null; reported numeric zero stays zero.",
        ),
        "per_capita_net_debt": (
            "Per-capita net debt distributed in the source workbook.",
            "current dollars per person",
            "Per Capita Net Debt",
            "Retain the reported numeric value; do not replace mismatches.",
            "'No data' becomes null.",
        ),
        "calculated_per_capita_net_debt": (
            "Audit comparison: reported net debt divided by reported population.",
            "current dollars per person",
            "Derived from net_debt and population_estimate",
            "net_debt / population_estimate when both are available.",
            "Null when either input is unavailable or population is not positive.",
        ),
        "tax_collection_pct": (
            "Previous calendar year's tax levy that was collected.",
            "percentage points",
            "% of Taxes Collected, CY [year]",
            "Multiply the source fraction by 100.",
            "'No data' becomes null.",
        ),
        "tax_collection_reference_year": (
            "Calendar year named in the tax-collection source header.",
            "year",
            "% of Taxes Collected, CY [year]",
            "Parse the four-digit CY year from the header.",
            "Never missing when the workbook contract passes.",
        ),
        "no_ufb_available": (
            "Source flag that NJ DCA has no User-Friendly Budget on file.",
            "boolean",
            "No UFB Available",
            "X becomes true; blank becomes false.",
            "Blank means the flag is not asserted, not that all data are complete.",
        ),
        "significant_data_missing": (
            "Source flag that at least one entire UFB section was blank.",
            "boolean",
            "Sig. Data Missing",
            "X becomes true; blank becomes false.",
            "Blank means the flag is not asserted.",
        ),
        "missingness_reason": (
            "Combined explanation of source flags and explicit 'No data' fields.",
            "text",
            "Source flags and field values",
            "Concatenate only observed source evidence; do not infer a cause.",
            "Blank when no source missingness evidence is present.",
        ),
        "total_structural_imbalances": (
            "Total of source-identified structural imbalances including offsets.",
            "current dollars",
            "Total Imbalances",
            "Convert numeric source value and round to cents.",
            "'No data' becomes null; retained as audit-only in v0.1.",
        ),
        "three_year_average_property_valuation": (
            "Three-year average total property valuation distributed by NJ DCA.",
            "current dollars",
            "3 Yr. Average Property Valuation",
            "Convert numeric cached source value; make no scale repair.",
            "'No data' becomes null; 2024 target values are audit-only.",
        ),
        "net_debt_to_valuation_pct": (
            "Source net debt divided by three-year average property valuation.",
            "percentage points",
            "Net Debt as % of 3 Year Avg Property Valuation",
            "Multiply the source fraction by 100; retain in the audit download "
            "but exclude from charts, summary tables, and interpretive claims.",
            "'No data' becomes null; 2024 values remain audit-only.",
        ),
        "publication_eligible_net_debt": (
            "Whether a reported net-debt point may appear in the public chart/table.",
            "boolean",
            "Derived quality-control field",
            "False for source flags, missing debt, or an unreconciled isolated zero.",
            "Never null.",
        ),
        "net_debt_publication_exclusion_reason": (
            "Visible reason a net-debt observation is not displayed.",
            "text",
            "Derived quality-control field",
            "Concatenate applicable evidence-based exclusion reasons.",
            "Blank when the observation is eligible.",
        ),
        "publication_eligible_tax_collection": (
            "Whether a tax-collection value may appear in the latest-valid table.",
            "boolean",
            "Derived quality-control field",
            "False for source flags or missing tax-collection value.",
            "Never null.",
        ),
        "tax_collection_publication_exclusion_reason": (
            "Visible reason a tax-collection observation is not displayed.",
            "text",
            "Derived quality-control field",
            "Concatenate applicable evidence-based exclusion reasons.",
            "Blank when the observation is eligible.",
        ),
        "source_workbook": (
            "Workbook filename used for the observation.",
            "text",
            "Build configuration",
            "Assign the pinned source filename.",
            "Never missing.",
        ),
        "source_sheet": (
            "Annual source sheet containing the observation.",
            "text",
            "Workbook sheet name",
            "Preserve the exact sheet name.",
            "Never missing.",
        ),
        "source_row": (
            "One-based row number in the annual source sheet.",
            "row number",
            "Workbook row position",
            "Record during extraction.",
            "Never missing.",
        ),
    }

    rows: list[dict[str, str]] = []
    for field in PANEL_COLUMNS:
        if field in specifications:
            description, unit, source, transformation, missing = specifications[
                field
            ]
        elif field.endswith("_source_cell"):
            metric = field.removesuffix("_source_cell")
            description = f"Excel cell address for {metric} in source_sheet."
            unit = "cell address"
            source = "Workbook coordinate"
            transformation = "Record column letter and one-based source row."
            missing = "Never missing when the workbook contract passes."
        elif field.endswith("_source_value"):
            metric = field.removesuffix("_source_value")
            description = (
                f"Auditable text representation of the source value for {metric}."
            )
            unit = "source representation"
            source = metric
            transformation = (
                "Preserve strings; format numeric source values without "
                "changing their meaning."
            )
            missing = "Blank source cells remain blank; 'No data' stays literal."
        else:
            raise RuntimeError(f"Data dictionary specification missing: {field}")
        rows.append(
            {
                "field": field,
                "description": description,
                "unit": unit,
                "source_field": source,
                "source_sheets": "2015 Summary through 2025 Summary",
                "transformation": transformation,
                "missing_data_rule": missing,
                "publication_role": (
                    "public metric"
                    if field in {"net_debt", "tax_collection_pct"}
                    else "traceability or audit field"
                ),
            }
        )
    return pd.DataFrame(rows)


def _format_currency(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.1f}M"
    return f"${value:,.0f}"


def _latest_table_html(latest: pd.DataFrame) -> str:
    rows: list[str] = []
    for record in latest.itertuples(index=False):
        rows.append(
            f"""
            <tr>
              <th scope="row">
                <span class="town-name">{html.escape(record.municipality_name)}</span>
                <span class="town-code">Code {html.escape(record.municipality_code)}</span>
              </th>
              <td data-label="Reported net debt">
                <span class="metric-value">{_format_currency(record.net_debt)}</span>
                <span class="metric-meta">Budget year {record.net_debt_budget_year}; current dollars</span>
              </td>
              <td data-label="Taxes collected">
                <span class="metric-value">{record.tax_collection_pct:.2f}%</span>
                <span class="metric-meta">CY {record.tax_collection_reference_year}, reported in budget year {record.tax_collection_budget_year}</span>
              </td>
              <td data-label="Source cells">
                <span class="source-cell">{html.escape(record.net_debt_source_sheet)} {html.escape(record.net_debt_source_cell)}</span>
                <span class="source-cell">{html.escape(record.tax_collection_source_sheet)} {html.escape(record.tax_collection_source_cell)}</span>
              </td>
            </tr>"""
        )
    return "\n".join(rows).strip()


def _debt_gap_summary(panel: pd.DataFrame) -> str:
    parts: list[str] = []
    for code, name in TARGET_MUNICIPALITIES.items():
        years = panel.loc[
            (panel["municipality_code"] == code)
            & ~panel["publication_eligible_net_debt"],
            "budget_year",
        ].tolist()
        if years:
            parts.append(f"{name}: {', '.join(str(int(year)) for year in years)}")
    return "; ".join(parts) + "."


def _render_template(template_name: str, replacements: dict[str, str]) -> str:
    template = (TEMPLATE_DIRECTORY / template_name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        template = template.replace("{{" + key + "}}", value)
    unresolved = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", template)))
    if unresolved:
        raise RuntimeError(
            f"Unresolved template fields in {template_name}: {unresolved}"
        )
    return template


def _write_source_zip(project_root: Path, destination: Path) -> None:
    included_files = [
        project_root / ".gitattributes",
        project_root / ".gitignore",
        project_root / "AI_USE.md",
        project_root / "CHANGELOG.md",
        project_root / "CONTRIBUTING.md",
        project_root / "LICENSE",
        project_root / "NOTICE.md",
        project_root / "README.md",
        project_root / "RELEASE_CHECKLIST.md",
        project_root / "pyproject.toml",
        project_root / "data" / "raw" / "README.md",
        project_root / "data" / "raw" / "source_manifest.json",
        *sorted((project_root / ".github").rglob("*.md")),
        *sorted((project_root / ".github").rglob("*.yml")),
        *sorted((project_root / ".github").rglob("*.yaml")),
        *sorted((project_root / "src" / "njpfo").rglob("*.py")),
        *sorted((project_root / "src" / "njpfo" / "templates").rglob("*")),
        *sorted((project_root / "tests").rglob("*.py")),
    ]
    files = sorted(
        {path for path in included_files if path.is_file()},
        key=lambda path: path.relative_to(project_root).as_posix(),
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in files:
            relative = path.relative_to(project_root).as_posix()
            info = zipfile.ZipInfo(
                f"nj-public-finance-observatory/{relative}",
                date_time=(2026, 7, 27, 0, 0, 0),
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes())


def _render_site(
    panel: pd.DataFrame,
    latest: pd.DataFrame,
    anomaly_ledger: pd.DataFrame,
    output_root: Path,
    project_root: Path,
) -> None:
    docs = output_root / "docs"
    assets = docs / "assets"
    downloads = docs / "downloads"
    assets.mkdir(parents=True, exist_ok=True)
    downloads.mkdir(parents=True, exist_ok=True)

    structural_coverage = int(
        panel["total_structural_imbalances"].notna().sum()
    )
    source_flag_count = int(
        (panel["no_ufb_available"] | panel["significant_data_missing"]).sum()
    )
    missing_debt_count = int(panel["net_debt"].isna().sum())
    common = {
        "SOURCE_SHA256": SOURCE_SHA256,
        "SOURCE_SHA256_SHORT": SOURCE_SHA256[:16],
        "SOURCE_RETRIEVAL_DATE": SOURCE_RETRIEVAL_DATE,
        "SOURCE_WORKBOOK_NAME": html.escape(SOURCE_WORKBOOK_NAME),
        "SOURCE_PAGE_URL": SOURCE_PAGE_URL,
        "SOURCE_WORKBOOK_URL": SOURCE_WORKBOOK_URL,
        "ANOMALY_COUNT": str(len(anomaly_ledger)),
        "STRUCTURAL_COVERAGE": f"{structural_coverage} of {len(panel)}",
        "SOURCE_FLAG_COUNT": str(source_flag_count),
        "MISSING_DEBT_COUNT": str(missing_debt_count),
        "DEBT_GAP_SUMMARY": html.escape(_debt_gap_summary(panel)),
    }
    index_replacements = {
        **common,
        "LATEST_TABLE_ROWS": _latest_table_html(latest),
    }
    (docs / "index.html").write_text(
        _render_template("index.html", index_replacements),
        encoding="utf-8",
        newline="\n",
    )
    (docs / "methods.html").write_text(
        _render_template("methods.html", common),
        encoding="utf-8",
        newline="\n",
    )
    shutil.copyfile(
        TEMPLATE_DIRECTORY / "site.css",
        assets / "site.css",
    )
    (docs / ".nojekyll").write_text("", encoding="utf-8", newline="\n")

    shutil.copyfile(
        output_root / "data" / "processed" / "mercer_fiscal_panel.csv",
        downloads / "mercer_fiscal_panel.csv",
    )
    shutil.copyfile(
        output_root / "data" / "data_dictionary.csv",
        downloads / "data_dictionary.csv",
    )
    shutil.copyfile(
        output_root / "data" / "anomaly_ledger.csv",
        downloads / "anomaly_ledger.csv",
    )
    _write_source_zip(project_root, downloads / "njpfo-source.zip")


def build_all(
    *,
    output_root: Path = PROJECT_ROOT,
    workbook_path: Path = RAW_WORKBOOK,
    project_root: Path = PROJECT_ROOT,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[Finding]]:
    output_root = Path(output_root).resolve()
    workbook_path = Path(workbook_path).resolve()
    project_root = Path(project_root).resolve()

    ensure_source(workbook_path)
    raw_records = extract_records(workbook_path)
    panel = normalize_records(raw_records)
    warnings = validate_panel(panel)
    anomaly_ledger = build_anomaly_ledger(panel)
    latest = build_latest_valid_table(panel)
    data_dictionary = build_data_dictionary()

    _write_csv(
        panel,
        output_root / "data" / "processed" / "mercer_fiscal_panel.csv",
    )
    _write_csv(
        latest,
        output_root / "data" / "processed" / "latest_valid_indicators.csv",
    )
    _write_csv(
        data_dictionary,
        output_root / "data" / "data_dictionary.csv",
    )
    _write_csv(
        anomaly_ledger.reindex(columns=ANOMALY_COLUMNS),
        output_root / "data" / "anomaly_ledger.csv",
    )
    build_chart(panel, output_root / "docs" / "assets" / "net_debt_trend.svg")
    _render_site(
        panel,
        latest,
        anomaly_ledger,
        output_root,
        project_root,
    )
    return panel, latest, anomaly_ledger, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild NJ Public Finance Observatory v0.1 artifacts."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Alternate output root for reproducibility testing.",
    )
    args = parser.parse_args()
    panel, latest, anomalies, warnings = build_all(output_root=args.output_root)
    print(
        f"Built {len(panel)} panel rows, {len(latest)} latest-valid rows, "
        f"and {len(anomalies)} anomaly-ledger entries."
    )
    if warnings:
        print(f"Validation warnings: {len(warnings)}")
        for finding in warnings:
            context = "/".join(
                value
                for value in (
                    finding.municipality_code,
                    str(finding.budget_year or ""),
                    finding.field,
                )
                if value
            )
            print(f"- [{finding.code}] {context}: {finding.message}")
    else:
        print("Validation warnings: 0")
    print(f"Artifacts written under: {Path(args.output_root).resolve()}")


if __name__ == "__main__":
    main()
