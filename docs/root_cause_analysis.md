# Root-Cause Investigation

## Metric Change

Monthly median resolution time for Firefox FIXED defects (fact_bug) jumped from **8.47 days in April 2024 to 14.39 days in May 2024** — a **+69.9%** month-over-month change, the largest single-month increase in the 10-month window. The following month (June) returned to 8.16 days.

## Initial Observation

The spike was isolated to May. April and June flanked it with sub-9-day medians. Three candidate drivers were tested: defect volume, severity mix, and component mix.

## Investigation

### Defect Volume

| Month | Defects | Median days |
|---|---|---|
| 2024-04 | 320 | 8.47 |
| 2024-05 | 272 | 14.39 |
| 2024-06 | 351 | 8.16 |

Volume dropped 15% in May. Smaller samples are noisier, but a 15% volume drop does not mechanically explain a 70% median increase.

### Severity Mix

| Month | High (S1+S2) % | Lower (S3+S4) % | Unclassified % |
|---|---|---|---|
| 2024-04 | 4.7% | 33.4% | 61.9% |
| 2024-05 | 6.6% | 31.3% | 62.1% |

Mix moved slightly: high-severity share rose ~1.9 percentage points, unclassified share unchanged. Note that per the Wilcoxon analysis, **high-severity defects resolve *faster***, so a shift *toward* high-severity would pull the median *down*. The May median moved in the opposite direction — severity mix cannot explain it.

### Component Mix

Top shifts in share and within-component median:

| Component | Apr share | May share | Share shift (pp) | Apr median | May median | Median change |
|---|---|---|---|---|---|---|
| Profile Backup | 10.9% | 3.3% | −7.6 | 15.6 d | 34.1 d | **×2.2** |
| Translations | 13.4% | 7.0% | −6.5 | 3.7 d | 12.1 d | **×3.3** |
| Messaging System | 11.3% | 14.3% | +3.1 | 12.1 d | 24.6 d | **×2.0** |
| PDF Viewer | 4.1% | 7.0% | +2.9 | 2.7 d | 11.1 d | **×4.1** |
| Sidebar | 5.9% | 8.5% | +2.5 | 35.4 d | 62.2 d | **×1.8** |
| New Tab Page | 6.6% | 9.2% | +2.6 | 17.0 d | 7.8 d | ×0.5 |

The dominant pattern is **not a share redistribution** — the biggest share-losers (Profile Backup −7.6pp, Translations −6.5pp) still saw their *per-component* medians double or triple. **The within-component median rose across most top components simultaneously.**

## Findings

- The April→May median jump is **not** attributable to severity mix.
- The jump is **not primarily** attributable to component mix either; several components whose share *fell* still showed sharply higher medians.
- The dominant pattern is a **cross-component, time-bound slowdown**: resolution times rose in May inside many separate components at once.
- Volume fell 15%, which may compound noise but does not mechanically produce the observed change.

## Interpretation

A cross-component slowdown in a single month is consistent with a **time-based external factor** affecting resolution capacity rather than defect quality. Plausible mechanisms, in rough order of likelihood for an open-source project in May:

- **Holiday / staffing capacity** — May contains Memorial Day (US) and Victoria Day (Canada); a reduced engineering week commonly shows up as elongated resolution tails.
- **Release-cycle events** — a Firefox release train in late April or early May could have redirected triage attention from steady-state bug work.
- **A category of defect not captured in our fields** (e.g. UX regressions, dependency updates) that happened to spike in May.

These are **hypotheses, not conclusions**. The Bugzilla fields available in this dataset do not include staffing, release calendar, or defect-category labels that would let us test them.

## Limitations

- Observational — the dataset shows association, not causation.
- No engineering-availability or release-schedule data in the pipeline.
- `resolution_days` is wall-clock, not active-engineering time; a staffing slowdown and a priority deferral look identical in this metric.
- 10-month window; one-off effects cannot be distinguished from recurring seasonal effects.
- Low-volume components with few bugs can have unstable medians; interpretation here focused on the top-10 by volume where that noise is bounded.
