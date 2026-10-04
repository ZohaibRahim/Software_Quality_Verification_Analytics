# Resume Bullets — Software Quality Verification Analytics

Based on actual measured results. Verified against `PROGRESS.md` and the SQL / R / Power BI outputs. Safe to copy to a resume.

---

**Software Quality Verification Analytics** · PostgreSQL · R · Power BI · DAX

- Modelled **3,000 Mozilla Firefox software defects** into a PostgreSQL star schema (1 fact + 4 conformed dims) and built a Power BI quality dashboard tracking defect arrivals, severity mix, component performance, and median resolution time (**9.56 days**).
- Tested the relationship between defect severity and resolution time in R using a **Wilcoxon rank-sum test**, finding that high-severity defects (S1+S2) resolved in a median of **8.86 days vs 13.61 days** for lower-severity (**p = 0.00038**, n = 1,173) — consistent with triage prioritization and reported as association rather than causation.
- Implemented **7 data-quality validation rules**, reconciled Power BI measures against SQL outputs (0 discrepancies), and investigated a **+69.9% month-over-month median resolution spike (Apr→May 2024)** — attributing it to a cross-component, time-based slowdown rather than a mix shift after decomposition by severity and component.
- Built a **Monte Carlo backlog forecast** in Python (5,000 trials, week-block resampling of real daily arrivals, bootstrap service times) and validated it with a **rolling walk-forward backtest** across four 2024 windows — **4 of 4 predicted 95% ranges contained the actual** backlog, mean |% error| = 7.7%. Bounded the effect of +50% staffing at a 6%–19% backlog reduction across returns-to-scale assumptions.

---

## Interview talking points (expanded)

- **Pipeline:** raw Bugzilla API → PostgreSQL staging → quarantine/cleaning view → star schema → R analysis + Power BI dashboard. Separation of concerns means cleaning is deterministic and re-runnable without re-hitting the API.
- **Why star schema in Postgres (not just a flat table):** Power BI's VertiPaq engine is optimized for star joins; dim surrogates isolate dimension changes from fact history; CALCULATE + dim relationships make DAX concise.
- **Why Wilcoxon:** resolution times are heavily right-skewed; non-parametric test ranks observations and is robust to outliers. Mean would have been misleading (High mean 32 d vs Lower mean 71 d — much larger gap than medians).
- **Why "association not causation":** severity is observational — bugs aren't randomly assigned a severity. The direction (high-severity resolves faster) is consistent with prioritization, not with severity *causing* fast resolution.
- **QA 7 — dashboard reconciliation:** critical rule. Every Power BI headline measure must equal the equivalent SQL under the same filter. Without this, a dashboard can silently diverge from source truth.
- **Root-cause finding:** ruled out the obvious hypotheses (severity mix moved the *wrong* way; component mix shifts were too small to explain a 70% median jump). The surviving pattern — simultaneous within-component slowdowns — is consistent with a time-bound capacity factor (holiday / release cycle / staffing), flagged as a hypothesis because the Bugzilla fields in scope don't let us test it.
