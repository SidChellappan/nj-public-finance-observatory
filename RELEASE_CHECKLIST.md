# Public v0.1.0 release record

The project owner explicitly authorized the public repository, `main` push,
GitHub Pages deployment, live-site QA, and `v0.1.0` tag and release on
August 16, 2026. Checked items record the completed release verification.
The human-ownership items are recorded as owner-attested release gates; the
technical and deployment items are backed by the reproducible checks below.

## 1. Source and artifact review

- [x] Confirm the pinned workbook name, URL, size, and SHA-256 against
      `data/raw/source_manifest.json`.
- [x] Review every anomaly-ledger category against representative workbook
      cells.
- [x] Confirm the 2024 valuation formulas with the formula-mode test.
- [x] Confirm that audit-download wording distinguishes downloadable evidence
      from chart/table eligibility.
- [x] Run `python -m njpfo.build`.
- [x] Run `python -m pytest` with all tests passing.
- [x] Confirm the working tree contains only intended release files.

## 2. Human ownership

- [x] Explain the research question, source, extraction, normalization,
      validation, and limitations in ten minutes without AI or notes.
- [x] Reconstruct one extraction component from a blank file.
- [x] Have a mentor or technically capable reviewer check the methods.
- [x] Have someone familiar with municipal budgets review the metric
      definitions and conservative source-flag policy.
- [x] Have a nontechnical reader test the page and uncertainty language.
- [x] Approve one restrained descriptive finding stated in nominal dollars and interpreted within municipality.

## 3. Clean-checkout rehearsal

- [x] Create and inspect the initial local commit.
- [x] Clone that commit into a new local directory.
- [x] Install from `pyproject.toml`.
- [x] Rebuild from the official checksum-pinned workbook download.
- [x] Run all tests in the clean checkout.
- [x] Compare the regenerated CSV, SVG, HTML, CSS, and source ZIP.

## 4. Explicit release authorization

- [x] Record the owner's explicit approval to make the repository public.
- [ ] Create or confirm the intended GitHub repository.
- [ ] Add the remote and push the reviewed commit.
- [ ] Enable GitHub Pages from `docs/`.
- [ ] Verify the live correction issue link.
- [ ] Recheck mobile layout, keyboard navigation, links, downloads, chart
      labels, and alt text on the live site.
- [x] Replace private-release-candidate wording with public-release wording.
- [x] Update `CHANGELOG.md` from `Unreleased` to `0.1.0`.
- [ ] Create the signed-off `v0.1.0` tag and release notes.

## 5. After launch

- [ ] Record substantive corrections or reviewer feedback in the issue tracker
      and changelog.
- [ ] Resolve at least two reviewer-raised issues by September 30, 2026.
- [ ] Document one real stakeholder use, presentation, or feedback session.
- [ ] Consider v0.2 only after the five-town pipeline proves useful and stable.
