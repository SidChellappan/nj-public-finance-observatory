# Public-finance expert review - decision log

**Reviewer:** Marc Pfeiffer
**Review status:** Substantive feedback received; revisions required before release. This is not an endorsement or a release approval.

The received email was not previously saved in this repository. This log records the decisions made from that correspondence; the original message should be retained with project correspondence if a complete review record is needed.

| Review point | Decision | Exact revision or rationale |
| --- | --- | --- |
| Explain the User-Friendly Budget (UFB). | **Accepted** | Add a plain-language introduction: the UFB is a New Jersey municipal budget reporting form/database, and its availability and completeness vary by municipality and year. Define `No UFB Available` and `Significant Data Missing` beside the source description. |
| Explain net debt, deductions, and tax collection. | **Accepted** | Add reader-facing definitions at first use. State that reported net debt is gross debt less the deductions recognized in the NJ DCA source; tax collection is the reported share of the prior calendar year's levy collected. |
| Explain the statutory context and limits of net debt. | **Accepted** | Add a limitation that reported net debt is a statutory, source-defined measure. It is not a complete measure of a local unit's total debt-like obligations, fiscal condition, or credit quality. Do not imply otherwise. |
| Account for county-improvement-authority lease or similar obligations. | **Deferred** | Do not add municipality-specific ACFR/authority debt analysis to v0.1. Instead, disclose that obligations not captured by the reported net-debt measure may exist and that assessing them would require separately reviewed ACFR disclosures and legal/financial analysis. |
| State the historical origin of net debt. | **Deferred** | The reviewer was not certain of the Great Depression origin. Do not make a historical-origin claim until it is verified against a primary legal or authoritative historical source. |
| Clarify "current dollars." | **Accepted** | Replace or pair the label with: "Nominal dollars as reported for each budget year; not adjusted for inflation or converted to a common-year dollar basis." Put this wording on the chart, latest-valid table, and methods page. |
| Treat the 2024 valuation-scale variation seriously. | **Accepted** | Keep all five 2024 valuation values and valuation-derived ratios out of charts, summary tables, and interpretive claims. Elevate this to a prominent data-quality note, explain that its cause is not established, and retain the raw values only for audit. |
| Characterize the valuation issue as user data-entry error. | **Declined** | There is no evidence establishing user entry as the cause. Describe it only as an unreconciled source-scale anomaly until NJ DCA or another authoritative source confirms its cause. |
| Current treatment of source flags. | **Accepted** | Preserve the separate `No UFB Available` and `Significant Data Missing` flags, keep flagged rows in the downloadable panel, and exclude them from public chart/latest-valid values under the documented publication rules. |
| Use raw net-debt differences to compare municipalities. | **Declined** | Do not present cross-municipality differences in reported net debt as a ranking, relative debt burden, fiscal-health finding, or evidence of a better/worse fiscal position. Reframe the chart as descriptive record inspection and within-municipality change, with this limitation stated prominently. |

## Release gate

Complete the accepted revisions, conduct an independent read-through for plain-language clarity and unsupported implications, and then request an explicit reviewer disposition if release approval is needed. The review does not itself authorize publication.

## Implementation status - August 13, 2026

The accepted pre-launch revisions recorded above have been implemented in the source templates and generators. The completed revision pass:

- explains the UFB and both source flags at first use;
- defines reported net debt and tax collection for ordinary readers;
- states the statutory, source-defined measurement boundary and the separately reviewed analysis that would be required to evaluate other debt-like obligations;
- uses the accepted nominal-dollar explanation on the chart, latest-valid table, methods page, and generated documentation;
- elevates the unreconciled 2024 valuation source-scale anomaly and states that its cause has not been established; and
- frames the chart as within-municipality record inspection, with an explicit guardrail against burden rankings or fiscal-strength comparisons.

The dataset, target municipalities, metrics, source-flag treatment, and publication-eligibility logic were not changed. A full rebuild produced 55 panel rows, 5 latest-valid rows, and 72 anomaly-ledger entries with the same 19 documented non-blocking source warnings. The complete automated suite passed 31 tests, and desktop/mobile visual and accessibility inspection was completed. An independent plain-language read-through found no remaining unsupported implication that reported net debt represents total obligations or that the chart ranks municipalities.

This records implementation and verification only. It is not a reviewer endorsement, an explicit reviewer disposition, owner authorization to publish, or release approval. Those gates remain separate.
