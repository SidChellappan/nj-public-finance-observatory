# Changelog

All notable project changes will be documented here.

## [Unreleased] - 2026-07-27

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

### Fixed

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
