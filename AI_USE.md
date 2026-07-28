# AI-use disclosure

AI assisted with:

- translating the project specification into a small Python package;
- drafting focused workbook-extraction and normalization code;
- proposing validation cases and automated tests;
- drafting the data dictionary, methods language, and accessible page structure;
- checking for internal consistency, broken links, and reproducibility; and
- identifying source values that warranted human review.

AI did **not** independently audit municipal submissions, confirm why any municipality's value changed, reconcile the workbook's external links, determine financial health, or approve a public claim.

A human remains responsible for:

- reading and understanding the NJ DCA glossary and source-sheet construction;
- verifying the five municipality codes and every field mapping;
- reviewing the anomaly ledger against the workbook cells;
- understanding and explaining the extraction, normalization, validation, and chart code;
- deciding whether an anomaly treatment is defensible;
- checking that the public language stays within the evidence;
- reviewing proposed corrections; and
- authorizing any push, deployment, public release, or tag.

The project treats generated code and prose as drafts that require testing and source-based review. Passing tests shows that the implemented contract is reproducible; it does not make the source data independently verified.
