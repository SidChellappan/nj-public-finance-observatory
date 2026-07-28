# Source-data and licensing notice

The MIT license in `LICENSE` covers the original project code, templates, and
documentation created for the NJ Public Finance Observatory.

It does not relicense the New Jersey Department of Community Affairs source
workbook or the public records contained in that workbook. The original
`UFB Database - FINAL.xlsm` remains an upstream NJ DCA artifact. It is kept
locally for audit work and intentionally excluded from Git.

The versioned source manifest records the publisher, official URL, retrieval
date, file size, and SHA-256 checksum. A clean build downloads that official
file and refuses to continue if its bytes do not match the reviewed source.

The processed CSVs transform and annotate the source records but do not make
the underlying municipal submissions independently verified. Reusers should:

1. cite NJ DCA as the source publisher;
2. preserve the project disclaimer and source provenance;
3. keep missing observations and source-quality flags visible;
4. avoid presenting audit-only fields as verified facts; and
5. consult the source publisher's terms before redistributing the original
   workbook.

These figures are not a credit rating, investment analysis, or policy
recommendation.
