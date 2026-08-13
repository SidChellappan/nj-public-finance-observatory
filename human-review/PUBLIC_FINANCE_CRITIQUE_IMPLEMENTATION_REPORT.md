# Public-finance critique implementation report

**Prepared:** August 13, 2026
**Purpose:** Map the decisions recorded in `PUBLIC_FINANCE_DECISION_LOG.md` to the v0.1 MVP that was described in `C:\Users\c_sid\Downloads\PF review.docx.pdf`.

## Executive conclusion

The MVP should be revised before launch. The decision log states that substantive feedback was received and that revisions are required before release. The accepted critiques do not require a new dataset, a new metric, a new backend, or a redesign of the extraction pipeline. They require clearer public definitions, stronger limitations, and more precise presentation language.

Two accepted treatments are already implemented in the data pipeline:

- source-flagged rows are preserved in the downloadable panel and excluded from chart and latest-valid values; and
- the five unreconciled 2024 valuation values and valuation-derived ratios are excluded from public presentation and claims.

Those two items still require clearer public explanation. The other accepted items require new or revised language in the homepage, chart, latest-valid table, methods page, data dictionary, and project documentation.

Public launch should remain blocked until the accepted revisions are implemented, the site is rebuilt, the automated tests pass, and an independent plain-language read-through finds no unsupported implications.

## Evidence reviewed

- The exact 13-page packet sent for review: `C:\Users\c_sid\Downloads\PF review.docx.pdf`.
- The internal decision log: `human-review/PUBLIC_FINANCE_DECISION_LOG.md`.
- The current MVP source templates, chart generator, table generator, data dictionary generator, README, tests, and generated `docs` pages.

The original reviewer email is not stored in the repository. The implementation below therefore relies on the decision log as the authoritative summary of the correspondence. The original email should be retained with private project correspondence for a complete audit trail; it should not be published without permission.

## What the critique changes

### 1. Explain the User-Friendly Budget at first use

**Decision:** Accepted.
**Problem in the sent paper:** Page 4 identifies the NJ DCA User-Friendly Budget Database but assumes the reader already understands what a UFB is. The source flags are explained later on page 6.

**Current MVP status:** Incomplete. The homepage names the database but does not introduce it. The methods page explains the two flags only after the extraction details.

**Required use in the MVP:** Add a short source explanation near the first mention on the homepage and at the start of the methods source section.

**Recommended wording:**

> The User-Friendly Budget (UFB) is New Jersey's municipal budget reporting form and database distributed by the Department of Community Affairs. Availability and completeness vary by municipality and budget year. "No UFB Available" means NJ DCA indicates that no UFB is on file; "Significant Data Missing" means a submitted UFB left at least one entire section blank.

**Primary locations:**

- `src/njpfo/templates/index.html`: hero/source-provenance area and the source-quality-flags card.
- `src/njpfo/templates/methods.html`: beginning of Source provenance, before technical workbook details.
- `README.md`: Primary source and provenance.

### 2. Define reported net debt and tax collection for ordinary readers

**Decision:** Accepted.
**Problem in the sent paper:** Page 5 contains definitions, but the public-facing chart and table on pages 9-10 still depend on the reader carrying those definitions forward.

**Current MVP status:** Partially complete. The methods page and data dictionary say net debt is gross debt less deductions and identify the tax reference year. The homepage does not define either measure when readers first encounter them.

**Required use in the MVP:** Put concise definitions immediately before the chart/latest-values section, while retaining the fuller definitions in Methods and the data dictionary.

**Recommended wording:**

> Reported net debt is the NJ DCA source measure of gross debt less the deductions recognized in that source for the budget year. Tax collection is the reported percentage of the prior calendar year's levy collected; the table therefore shows both the tax reference year and the associated budget year.

**Primary locations:**

- `src/njpfo/templates/index.html`: Read this first or immediately before the chart.
- `src/njpfo/templates/methods.html`: Source sheets and fields.
- `src/njpfo/build.py`: generated data-dictionary definitions, to keep the downloadable documentation consistent.

### 3. Add the statutory/source-defined limitation and disclose omitted obligations

**Decision:** The limitation was accepted; municipality-specific authority/lease analysis was deferred.
**Problem in the sent paper:** Pages 5 and 11 warn that net debt is not total liabilities or a complete statement of financial position, but they do not clearly explain that this is a statutory/source-defined measure or that other debt-like and lease-backed obligations can require separate review.

**Current MVP status:** Incomplete. General fiscal-health and creditworthiness disclaimers exist, but the specific measurement boundary is missing.

**Required use in the MVP:** Add a prominent limitation without adding ACFR, county-improvement-authority, or municipality-specific obligation analysis to v0.1.

**Recommended wording:**

> Reported net debt is a statutory, source-defined measure. It is not a complete measure of a local unit's total debt-like obligations, fiscal condition, or credit quality. Obligations not captured by this field may exist; evaluating them would require separately reviewed ACFR disclosures and legal and financial analysis, which v0.1 does not perform.

This disclosure implements the accepted limitation while respecting the decision to defer a new ACFR/authority research layer.

**Primary locations:**

- `src/njpfo/templates/index.html`: What the data can and cannot show.
- `src/njpfo/templates/methods.html`: Known limitations.
- `README.md`: Known limitations and disclaimer.
- `src/njpfo/build.py`: net-debt data-dictionary definition or limitation field, if the existing schema can express it without adding a new column.

### 4. Replace vague "current dollars" wording with the accepted nominal-dollar explanation

**Decision:** Accepted.
**Problem in the sent paper:** Pages 3, 5, 9, 10, and 11 use "current dollars" or "current-dollar" repeatedly. The reviewer requested wording that makes the absence of inflation adjustment and common-year conversion unmistakable.

**Current MVP status:** Not implemented. The homepage, chart description, latest-valid rows, methods page, README, and data dictionary still use "current dollars."

**Required use in the MVP:** Use the decision log's accepted sentence consistently wherever debt values are presented.

**Required wording:**

> Nominal dollars as reported for each budget year; not adjusted for inflation or converted to a common-year dollar basis.

**Primary locations:**

- `src/njpfo/templates/index.html`: chart note, figure caption, and latest-valid table explanation.
- `src/njpfo/chart.py`: chart title/subtitle or y-axis context, SVG title, and SVG description.
- `src/njpfo/build.py`: latest-valid table row metadata and data-dictionary unit/definition text.
- `src/njpfo/templates/methods.html`: field table, publication rules, and limitations.
- `README.md`: field map and limitations.

The wording should appear in visible text, not only in a tooltip or download.

### 5. Elevate the 2024 valuation issue without inventing its cause

**Decision:** Treatment accepted; data-entry-error characterization declined.
**Problem in the sent paper:** Pages 5, 7, 8, and 11 document the anomaly, but the critique asks the release to give it greater prominence and to make clear that its cause is unknown.

**Current MVP status:** Behaviorally complete but linguistically incomplete. The homepage already has a dedicated anomaly card and the methods page excludes the affected values and ratios. Neither says plainly that the cause has not been established. The homepage heading "2024 valuation scale problem" is less precise than the decision-log term.

**Required use in the MVP:** Rename the note and add an explicit no-cause statement.

**Recommended wording:**

> Unreconciled 2024 valuation-source anomaly. All five 2024 three-year property-valuation values are sharply below adjacent years and rely on cached external-workbook lookups. The cause has not been established. The raw values remain available only for audit; the values and valuation-derived ratios are excluded from charts, summary tables, and interpretive claims.

Do not call the issue a user error, municipal error, or NJ DCA error unless an authoritative source establishes that cause.

**Primary locations:**

- `src/njpfo/templates/index.html`: the existing valuation anomaly card.
- `src/njpfo/templates/methods.html`: Source provenance, Publication rules, and Known limitations.
- `README.md`: Confirmed source-data problems.
- `data/anomaly_ledger.csv` generation text, if any entry currently implies an established cause.

No extraction or publication-eligibility rule needs to change.

### 6. Preserve the accepted source-flag treatment

**Decision:** Accepted.
**Problem assessed in the sent paper:** Pages 6-7 asked whether it is defensible to preserve the two NJ DCA flags, retain flagged rows, and exclude flagged observations from public chart/latest-valid values.

**Current MVP status:** Implemented. The processed panel preserves both flags. Flagged rows remain downloadable and cannot supply displayed debt or tax values. Automated tests already cover these rules.

**Required use in the MVP:** Keep the existing logic. Improve only the reader-facing explanation by placing the flag definitions beside the first UFB description. Do not merge the flags, drop flagged rows, or convert missingness to zero.

**Primary locations to preserve:**

- `src/njpfo/normalize.py`: publication rules.
- `src/njpfo/validate.py`: validation and anomaly ledger.
- `tests/test_schema.py` and `tests/test_targets.py`: source-flag publication protections.

### 7. Prevent the chart from becoming a cross-municipality burden ranking

**Decision:** The proposed use of raw net-debt differences for municipal comparison was declined.
**Problem in the sent paper:** Pages 9-10 place all municipalities on one chart and summarize which had higher or lower later endpoints. Although the packet includes guardrails, readers can still mistake vertical differences for relative debt burden or fiscal strength.

**Current MVP status:** Mostly restrained. The current homepage does not reproduce the paper's endpoint table or higher/lower summary. It does, however, display all five series together and says values "move over time" without explicitly telling readers to interpret each line within municipality.

**Required use in the MVP:** Keep the chart, but add this guardrail directly below it:

> Read each series as a within-municipality record over time. Differences in line height between municipalities are not measures of relative debt burden, fiscal strength, or a better or worse fiscal position.

Do not add rankings, comparative burden claims, or a cross-municipality winner/loser summary. If an endpoint statement is retained later, make it explicitly municipality-specific and nominal, and do not compare the magnitude of changes across towns.

## Items that should not expand v0.1

- Do not add county-improvement-authority, lease-obligation, ACFR, or authority-debt data before launch. Add only the limitation disclosure.
- Do not state a Great Depression or other historical origin for net debt without verification from a primary legal or authoritative historical source.
- Do not identify the 2024 valuation anomaly as user data-entry error.
- Do not add rankings, scores, relative-debt-burden comparisons, credit judgments, or fiscal-health conclusions.

## Exact MVP change set

### Public homepage

1. Add the plain-language UFB explanation near the first source reference.
2. Define net debt and tax collection before the first chart/table use.
3. Replace "Current dollars" with the accepted nominal-dollar sentence.
4. Add the statutory/source-defined and omitted-obligations limitation.
5. Rename and strengthen the 2024 valuation note, including that the cause is not established.
6. Add the within-municipality chart guardrail.
7. Keep the source-flag behavior and downloadable audit evidence unchanged.

### Methods page

1. Introduce the UFB before workbook mechanics.
2. Repeat the reader-facing metric definitions.
3. Add the statutory measurement boundary and deferred-obligations disclosure.
4. Use the accepted nominal-dollar language in fields, publication rules, and limitations.
5. State that the valuation anomaly's cause is unknown.
6. Retain the exact source-flag and audit rules.

### Generated artifacts and documentation

1. Update `chart.py` so the SVG's visible labels and accessibility metadata reflect nominal dollars and within-municipality interpretation.
2. Update `build.py` so latest-table metadata and the generated data dictionary use the same wording.
3. Update `README.md` and `CHANGELOG.md` so the review-driven revisions are reproducible and visible in version history.
4. Rebuild `docs/index.html`, `docs/methods.html`, the SVG, data dictionary, and public download bundle from source. Do not hand-edit generated files.

## Verification required after implementation

1. Add focused assertions that both public pages contain the nominal-dollar explanation and statutory/source-defined limitation.
2. Assert that the public pages say the cause of the 2024 valuation anomaly is not established.
3. Preserve the existing source-flag and valuation-exclusion tests.
4. Rebuild with `python -m njpfo.build` from the repository virtual environment.
5. Run the full automated test suite.
6. Inspect the regenerated homepage and methods page on desktop and mobile widths.
7. Conduct an independent plain-language read-through focused on whether a reader could mistake reported net debt for total obligations or the chart for a municipal ranking.
8. Record the completed revisions in the decision log or changelog and then resolve the public-finance release gate.

## Launch judgment

The accepted critiques are material to accurate interpretation, so they should be incorporated before user testing and public launch. They are a bounded final revision pass, not a request to rebuild the project. Once these language changes are made, rebuilt, and verified, the MVP can proceed to nontechnical user testing and release authorization without adding new scope.
