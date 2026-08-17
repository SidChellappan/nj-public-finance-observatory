# NJ Public Finance Observatory v0.1

A methods-first civic research project that asks:

> How have reported municipal net debt and tax-collection indicators changed across five Mercer County municipalities from 2015-2025, and where does the public record contain gaps or inconsistencies?

The five municipalities are Hamilton (`1103`), Lawrence (`1107`), Trenton (`1111`), West Windsor (`1113`), and Princeton (`1114`). Municipality codes are the stable keys. The pipeline never joins records using names alone.

The project is deliberately narrow:

- 5 municipalities
- 11 annual Summary sheets, 2015-2025
- 55 municipality-year rows, including missing rows
- 1 principal chart: reported net debt
- 1 supporting table: latest valid debt and tax-collection observations

It does not rank communities, create a fiscal-health score, make causal or predictive claims, or give credit, investment, or policy advice.

## Install

Python 3.11 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On macOS or Linux, activate the environment with `source .venv/bin/activate`.

## Rebuild everything

From the repository root, run:

```text
python -m njpfo.build
```

That command:

1. verifies the pinned workbook checksum, downloading the official file only if it is absent;
2. extracts the five target codes from `2015 Summary` through `2025 Summary`;
3. normalizes the 55-row panel without imputing missing values;
4. enforces the data contract and records non-blocking anomalies;
5. regenerates the processed panel, latest-valid table, data dictionary, anomaly ledger, SVG chart, static pages, and public download copies; and
6. creates a deterministic source-code ZIP for the static site.

The source workbook is large, so a clean build may take roughly a minute.

## Run tests

```text
python -m pytest
```

The tests cover duplicate keys, missing codes and rows, the 55-row contract, invalid years, negative values, conversion of `"No data"` to null rather than zero, per-capita consistency warnings, roughly 100x percentage-scale changes, source-flagged publication attempts, field-specific publication statuses, the five 2024 external-workbook valuation formulas, missing-row preservation, latest-valid selection, and byte-for-byte reproduction of the public artifacts from the pinned workbook.

## Primary source and provenance

The User-Friendly Budget (UFB) is New Jersey's municipal budget reporting form and database distributed by the Department of Community Affairs. Availability and completeness vary by municipality and budget year. `No UFB Available` means NJ DCA indicates that no UFB is on file; `Significant Data Missing` means a submitted UFB left at least one entire section blank.

- Publisher: New Jersey Department of Community Affairs, Division of Local Government Services
- Source page: <https://www.nj.gov/dca/dlgs/programs/mc_budgets.shtml>
- Workbook: `UFB Database - FINAL.xlsm`
- Workbook URL: <https://www.nj.gov/dca/dlgs/programs/mc_budget_docs/UFB%20Database%20-%20FINAL.xlsm>
- Retrieved: 2026-07-27
- File size: 22,644,255 bytes
- SHA-256: `79a59be4c4ab2669d60ebb8072aab5a5775df7025e66cb95a887e1c39ed8ccaa`

The downloaded workbook is preserved locally in `data/raw/` but intentionally excluded from Git. The versioned `data/raw/README.md` and `data/raw/source_manifest.json` record sufficient provenance for a clean checkout to download and verify the official file. The build stops if the checksum changes so a replaced upstream workbook cannot silently alter generated artifacts.

## Source sheets and discovered fields

| Field | 2015-2024 | 2025 | Treatment |
|---|---:|---:|---|
| Municipality code | A | A | Four-digit stable key |
| Municipality name | C | C | Source label preserved; display name mapped by code |
| No UFB Available | F | F | Source flag |
| Significant Data Missing | G | G | Source flag |
| Population | I | I | Annual header label preserved |
| Taxes collected | P | P | Source fraction multiplied by 100 |
| Net debt | LU | LT | Reported nominal dollars; primary measure |
| Per-capita net debt | LV | LU | Reported nominal dollars per person; audit field |
| Three-year property valuation | LW | LV | Reported nominal dollars; audit-only in v0.1 |
| Debt as percent of valuation | LX | LW | Included in the audit download; excluded from charts, summary tables, and interpretive claims |
| Total structural imbalances | OQ | OP | Reported nominal dollars; included audit-only after definition and coverage review |

Reported net debt is the NJ DCA source measure of gross debt less the deductions recognized in that source for the budget year. Tax collection is the reported percentage of the prior calendar year's levy collected. The processed panel therefore stores both the tax reference year and the associated budget year.

Nominal dollars as reported for each budget year; not adjusted for inflation or converted to a common-year dollar basis.

## Field and missing-data rules

- The exact source text `"No data"` becomes null, never numeric zero.
- Rows are never dropped because a metric is missing.
- Numeric zeros distributed by the workbook remain zeros. They are not silently reclassified as missing.
- `No UFB Available` and `Significant Data Missing` remain separate boolean fields with their NJ DCA glossary meanings.
- A source-flagged row remains in the panel but cannot supply a public chart point or latest-valid table value.
- The workbook's reported per-capita value remains separate from the project's `net_debt / population` audit calculation.
- The source's percent-formatted fractions are converted to percentage points by multiplying by 100.
- Every metric keeps its source workbook, sheet, row, cell, original representation, unit, and documented transformation.
- Suspicious values are retained and described in `data/anomaly_ledger.csv`; they are not silently repaired.
- The complete processed CSV is an audit download. A field can appear there while remaining ineligible for the chart, latest-valid table, or interpretive claims.

See `data/data_dictionary.csv` and `docs/methods.html` for field-level definitions.

## Confirmed source-data problems

1. **Trenton missing debt.** Trenton's 2025 debt fields say `"No data"`. Trenton also has earlier missing or unavailable debt observations. They remain null and appear as chart gaps.
2. **Unreconciled 2024 valuation source-scale anomaly.** Each target's 2024 three-year property valuation is far below both adjacent years. A formula-mode regression test verifies that those five cells are external-workbook `VLOOKUP` references. The cause has not been established. The raw values remain available only for audit; the values and valuation-derived ratios are excluded from charts, summary tables, and interpretive claims.
3. **Princeton 2022 zero.** The source row reports numeric zero for every net-debt component while adjacent years exceed $90 million, and the property valuation says `"No data"`. The zero remains in the processed panel but is excluded from the chart pending clarification.
4. **Per-capita mismatches.** Several distributed per-capita net-debt values differ by more than 5% from reported debt divided by the population in the same row. Both fields remain in the audit download; per-capita debt is excluded from v0.1 charts, summary tables, and interpretive claims.
5. **Broad source flags.** A `Significant Data Missing` flag can describe an unobserved blank section elsewhere in the row. v0.1 takes the conservative publication rule of excluding any flagged row from the chart and latest-valid table.

These issues are evidence about the source record, not evidence of municipal failure.

## Known limitations

- Reported net debt is a statutory, source-defined measure. It is not a complete measure of a local unit's total debt-like obligations, fiscal condition, or credit quality. Obligations not captured by this field may exist; evaluating them would require separately reviewed ACFR disclosures and legal and financial analysis, which v0.1 does not perform.
- Municipal values are self-reported public budget records and are not independently audited here.
- The project cannot establish causation, management quality, fiscal health, or creditworthiness.
- Nominal dollars as reported for each budget year; not adjusted for inflation or converted to a common-year dollar basis.
- A missing or excluded point does not mean zero.
- Source definitions and workbook construction may change between releases.
- `openpyxl` reads cached workbook values; it does not execute macros or refresh external links.
- Total structural imbalances are included only as an audit field. v0.1 makes no claim about what a positive or zero value implies.

### Why ACS is excluded

ACS five-year estimates introduce overlapping estimate periods, margins of error, vintage choices, and a separate geographic matching contract. Adding them before the base municipal workbook is stable would create more interpretation than the v0.1 question needs. ACS endpoint comparisons can be reviewed for v0.2.

### Why EMMA is excluded

EMMA adds issuer matching, disclosure-document extraction, security-level context, ratings, and trade data. Those are valuable but separate research problems. They should not be attached to this panel until the base NJ DCA extraction has a real user and a stable correction process.

## Public artifacts

- `data/processed/mercer_fiscal_panel.csv` — complete 55-row audit panel, including flagged and audit-only fields
- `data/processed/latest_valid_indicators.csv` — five-row supporting table with source cells
- `data/data_dictionary.csv` — field definitions, units, transformations, and missingness rules
- `data/anomaly_ledger.csv` — field-level issues, treatments, publication status, and source cells
- `docs/assets/net_debt_trend.svg` — accessible reported-net-debt chart
- `docs/index.html` — responsive static page
- `docs/methods.html` — methods, provenance, field map, validation, and limitations

## Submit a correction

A reproducible correction should use the [structured GitHub data-correction form](https://github.com/SidChellappan/nj-public-finance-observatory/issues/new?template=data-correction.yml) and include:

1. municipality code;
2. budget year;
3. field name;
4. source sheet and cell;
5. the current Observatory record;
6. proposed correction; and
7. a public source link, precise citation, or public attachment supporting the change.

GitHub issues and attachments are public, so do not submit confidential, private, or personally identifying information. See `CONTRIBUTING.md` for the review workflow.

An accepted correction should update the anomaly ledger or extraction rule, add a regression test when useful, rebuild every artifact, preserve the prior result in version history, and receive a plain-language changelog entry. Opening an issue does not automatically replace a source-reported value.

## Licensing and source rights

The original project code, templates, and documentation are available under
the MIT license in `LICENSE`. The upstream NJ DCA workbook is not relicensed by
this project and is intentionally excluded from Git. See `NOTICE.md` for the
source-data and reuse notice.

## Disclaimer

> These figures come from self-reported public budget records and have not been independently audited. Reported net debt is a statutory, source-defined measure, not a complete measure of total debt-like obligations, fiscal condition, or credit quality. This project is not a credit rating, investment analysis, or policy recommendation.
