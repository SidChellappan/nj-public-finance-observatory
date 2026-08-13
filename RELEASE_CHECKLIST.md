# Public v0.1 release checklist

This repository remains a private release candidate until every required box
below is checked by the project owner. Do not push, deploy, publish, or create
the `v0.1.0` tag merely because the automated tests pass.

## 1. Source and artifact review

- [ ] Confirm the pinned workbook name, URL, size, and SHA-256 against
      `data/raw/source_manifest.json`.
- [ ] Review every anomaly-ledger category against representative workbook
      cells.
- [ ] Confirm the 2024 valuation formulas with the formula-mode test.
- [ ] Confirm that audit-download wording distinguishes downloadable evidence
      from chart/table eligibility.
- [ ] Run `python -m njpfo.build`.
- [ ] Run `python -m pytest` with all tests passing.
- [ ] Confirm the working tree contains only intended release files.

## 2. Human ownership

- [ ] Explain the research question, source, extraction, normalization,
      validation, and limitations in ten minutes without AI or notes.
- [ ] Reconstruct one extraction component from a blank file.
- [ ] Have a mentor or technically capable reviewer check the methods.
- [ ] Have someone familiar with municipal budgets review the metric
      definitions and conservative source-flag policy.
- [ ] Have a nontechnical reader test the page and uncertainty language.
- [ ] Approve one restrained descriptive finding stated in nominal dollars and interpreted within municipality.

## 3. Clean-checkout rehearsal

- [ ] Create and inspect the initial local commit.
- [ ] Clone that commit into a new local directory.
- [ ] Install from `pyproject.toml`.
- [ ] Rebuild from the official checksum-pinned workbook download.
- [ ] Run all tests in the clean checkout.
- [ ] Compare the regenerated CSV, SVG, HTML, CSS, and source ZIP.

## 4. Explicit release authorization

- [ ] Record the owner's explicit approval to make the repository public.
- [ ] Create or confirm the intended GitHub repository.
- [ ] Add the remote and push the reviewed commit.
- [ ] Enable GitHub Pages from `docs/`.
- [ ] Verify the live correction issue link.
- [ ] Recheck mobile layout, keyboard navigation, links, downloads, chart
      labels, and alt text on the live site.
- [ ] Replace private-release-candidate wording with public-release wording.
- [ ] Update `CHANGELOG.md` from `Unreleased` to `0.1.0`.
- [ ] Create the signed-off `v0.1.0` tag and release notes.

## 5. After launch

- [ ] Record substantive corrections or reviewer feedback in the issue tracker
      and changelog.
- [ ] Resolve at least two reviewer-raised issues by September 30, 2026.
- [ ] Document one real stakeholder use, presentation, or feedback session.
- [ ] Consider v0.2 only after the five-town pipeline proves useful and stable.
