# Changelog

All notable project changes will be documented here.

## [Unreleased] - 2026-08-13

### Added

- Pinned NJ DCA 2025 User-Friendly Budget Database with retrieval provenance and SHA-256 verification.
- Reproducible extraction of five Mercer County municipality codes from the 2015-2025 Summary sheets.
- Complete 55-row processed panel preserving missing observations and source representations.
- Data dictionary, latest-valid indicator table, and field-level anomaly ledger.
- Build-stopping contract validation and non-blocking anomaly warnings.
- Automated schema, target, metric, publication-safety, and clean-rebuild tests.
- Accessible reported-net-debt SVG with visible gaps and no interpolation.
- Responsive static observation and methods pages suitable for GitHub Pages.
- AI-use disclosure, correction protocol, and deterministic public download bundle.
- Structured GitHub data-correction issue form and contribution workflow.
- Formula-mode regression coverage for the five 2024 external valuation lookups.
- MIT code license, source-data notice, raw-workbook Git policy, and public-release checklist.

### Changed

- Implemented the accepted pre-launch public-finance review revisions without changing the dataset, target municipalities, metrics, source-flag rules, or publication-eligibility logic.
- Added first-use explanations of the User-Friendly Budget and its two distinct source flags, plus reader-facing definitions of reported net debt and tax collection.
- Added the statutory, source-defined net-debt boundary and disclosed that evaluating other debt-like obligations would require separately reviewed ACFR disclosures and legal and financial analysis outside v0.1.
- Replaced vague current-dollar wording with the accepted nominal-dollar explanation in the chart, latest-valid table, methods, data dictionary, and project documentation.
- Reframed the chart as within-municipality record inspection and added a guardrail against treating line height as relative debt burden, fiscal strength, or a municipal ranking.
- Elevated the unreconciled 2024 valuation source-scale anomaly, stated that its cause has not been established, and retained the existing audit-only and public-exclusion treatment.
- Expanded automated language and SVG accessibility assertions for the accepted interpretation safeguards.

### Fixed

- Restored horizontal scrolling for the Methods field-location table at mobile widths so all source columns remain reachable.
- Made anomaly-ledger publication statuses field-specific so a missing tax value
  does not imply that a valid net-debt chart point is excluded.
- Clarified that audit-only evidence remains in the downloadable panel while
  staying excluded from charts, summary tables, and interpretive claims.

### Source issues documented

- Trenton debt and tax fields reported as `"No data"` in 2025 and selected earlier years.
- Unreconciled 2024 property-valuation scale anomaly from cached external-workbook lookups.
- Princeton 2022 numeric zero net debt between positive adjacent years.
- Reported per-capita net-debt values that do not match same-row debt divided by population within 5%.

### Release status

- Private release candidate only. No push, deployment, publication, release, or `v0.1.0` tag has been authorized.
