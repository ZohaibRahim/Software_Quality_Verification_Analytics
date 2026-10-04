# Resume Bullets — Software Quality Verification Analytics

Based on actual measured results. Verified against `PROGRESS.md` and the SQL / R / Power BI outputs. Safe to copy to a resume.

---

**Software Quality Verification Analytics** · PostgreSQL · R · Power BI · DAX

- Modelled **3,000 Mozilla Firefox software defects** into a PostgreSQL star schema (1 fact + 4 conformed dims) and built a Power BI quality dashboard tracking defect arrivals, severity mix, component performance, and median resolution time (**9.56 days**).
- Tested the relationship between defect severity and resolution time in R using a **Wilcoxon rank-sum test**, finding that high-severity defects (S1+S2) resolved in a median of **8.86 days vs 13.61 days** for lower-severity (**p = 0.00038**, n = 1,173) — consistent with triage prioritization and reported as association rather than causation.
- Implemented **7 data-quality validation rules**, reconciled Power BI measures against SQL outputs (0 discrepancies), and investigated a **+69.9% month-over-month median resolution spike (Apr→May 2024)** — attributing it to a cross-component, time-based slowdown rather than a mix shift after decomposition by severity and component.
- Built a **Monte Carlo backlog-forecast simulation** in Python with staffing elasticity (α ∈ {0.3, 0.6, 1.0}) and verified it with a **walk-forward backtest** — training on Jan–Jun 2024 and predicting Jul–Sep 2024 produced a **95% range of [230, 293] open defects at test end vs actual 231** (−12.8% error, inside the predicted range). Headline forecast: +50% staffing cuts baseline backlog by 6%–19% depending on returns-to-scale.

---

## Interview talking points (expanded)

- **Pipeline:** raw Bugzilla API → PostgreSQL staging → quarantine/cleaning view → star schema → R analysis + Power BI dashboard. Separation of concerns means cleaning is deterministic and re-runnable without re-hitting the API.
- **Why star schema in Postgres (not just a flat table):** Power BI's VertiPaq engine is optimized for star joins; dim surrogates isolate dimension changes from fact history; CALCULATE + dim relationships make DAX concise.
- **Why Wilcoxon:** resolution times are heavily right-skewed; non-parametric test ranks observations and is robust to outliers. Mean would have been misleading (High mean 32 d vs Lower mean 71 d — much larger gap than medians).
- **Why "association not causation":** severity is observational — bugs aren't randomly assigned a severity. The direction (high-severity resolves faster) is consistent with prioritization, not with severity *causing* fast resolution.
- **QA 7 — dashboard reconciliation:** critical rule. Every Power BI headline measure must equal the equivalent SQL under the same filter. Without this, a dashboard can silently diverge from source truth.
- **Root-cause finding:** ruled out the obvious hypotheses (severity mix moved the *wrong* way; component mix shifts were too small to explain a 70% median jump). The surviving pattern — simultaneous within-component slowdowns — is consistent with a time-bound capacity factor (holiday / release cycle / staffing), flagged as a hypothesis because the Bugzilla fields in scope don't let us test it.
