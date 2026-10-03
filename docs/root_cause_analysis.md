# Root-Cause Investigation

> **Status:** skeleton. Content will be filled once a real metric movement is identified in the data (STEPS 19–20 in `PROGRESS.md`). Do not fabricate numbers.

## Metric Change

_Describe the specific metric and the two periods being compared. Example: median resolution days rose from X.X to Y.Y between <month A> and <month B>._

## Initial Observation

_Short paragraph framing why this change matters._

## Investigation

### Defect Volume
_Compare total defect counts in each period._

### Severity Mix
_Compare the share of S1/S2/S3/S4 and the derived High vs Lower groups._

### Component Mix
_Identify components whose share changed materially between the two periods, and show each component's median resolution days._

## Findings

_1–3 bullet points describing which factors moved in parallel with the metric. Use language such as "coincided with", "associated with", "appears to contribute" — not causal._

## Interpretation

_Business-level interpretation. State clearly that this is an association, not a cause._

## Limitations

- Observational analysis — no causal claim.
- Resolution time includes non-engineering waits.
- Small-sample components can distort medians.
- Public proxy dataset.
