# =============================================================================
# hypothesis_test.R
#
# Purpose: Compare resolution-time distributions for High-severity (S1+S2) vs
#          Lower-severity (S3+S4) Firefox defects using the Wilcoxon rank-sum
#          (Mann-Whitney U) test.
#
# Stage:   STEPS 12-14 (master project brief §18-§20)
#
# Inputs:  data/processed/analysis_dataset.csv   (produced by sql/06_analysis_queries.sql)
# Outputs: console summary + diagnostic plots in images/
#
# Status:  SKELETON. Run only once a real analysis_dataset.csv exists.
# =============================================================================

# ---- 0. Setup ---------------------------------------------------------------
# install.packages(c("readr","dplyr","ggplot2"))
suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
})

input_path <- file.path("data", "processed", "analysis_dataset.csv")

if (!file.exists(input_path)) {
  stop("analysis_dataset.csv not found. Run sql/06_analysis_queries.sql export first.")
}

bugs <- readr::read_csv(input_path, show_col_types = FALSE)

# ---- 1. Define groups -------------------------------------------------------
bugs <- bugs %>%
  mutate(severity_group = dplyr::case_when(
    severity %in% c("S1", "S2") ~ "High",
    severity %in% c("S3", "S4") ~ "Lower",
    TRUE                        ~ "Unclassified"
  )) %>%
  filter(severity_group %in% c("High", "Lower"))

# ---- 2. Exploratory statistics ---------------------------------------------
summary_stats <- bugs %>%
  group_by(severity_group) %>%
  summarise(
    n       = dplyr::n(),
    median  = median(resolution_days, na.rm = TRUE),
    mean    = mean(resolution_days,   na.rm = TRUE),
    sd      = sd(resolution_days,     na.rm = TRUE),
    p25     = quantile(resolution_days, 0.25, na.rm = TRUE),
    p75     = quantile(resolution_days, 0.75, na.rm = TRUE),
    .groups = "drop"
  )
print(summary_stats)

# ---- 3. Diagnostic plots ---------------------------------------------------
dir.create("images", showWarnings = FALSE)

ggplot(bugs, aes(x = resolution_days, fill = severity_group)) +
  geom_histogram(position = "identity", alpha = 0.5, bins = 40) +
  labs(title = "Resolution-time distribution by severity group",
       x = "Resolution days", y = "Count") +
  theme_minimal()
ggsave("images/hist_resolution_by_severity.png", width = 7, height = 4, dpi = 150)

ggplot(bugs, aes(x = severity_group, y = resolution_days)) +
  geom_boxplot() +
  scale_y_log10() +
  labs(title = "Resolution days by severity group (log-scale)",
       x = NULL, y = "Resolution days (log10)") +
  theme_minimal()
ggsave("images/box_resolution_by_severity.png", width = 6, height = 4, dpi = 150)

# ---- 4. Hypothesis test ----------------------------------------------------
# H0: resolution-time distributions do not differ between High and Lower groups.
# H1: they do differ.
# alpha = 0.05.
test_result <- wilcox.test(
  resolution_days ~ severity_group,
  data        = bugs,
  exact       = FALSE,
  correct     = TRUE,
  alternative = "two.sided"
)
print(test_result)

# ---- 5. Reporting ----------------------------------------------------------
med_high  <- summary_stats$median[summary_stats$severity_group == "High"]
med_lower <- summary_stats$median[summary_stats$severity_group == "Lower"]

cat("\n--- Business summary ---\n")
cat(sprintf("High-severity median:  %.2f days (n=%d)\n",
            med_high,  summary_stats$n[summary_stats$severity_group == "High"]))
cat(sprintf("Lower-severity median: %.2f days (n=%d)\n",
            med_lower, summary_stats$n[summary_stats$severity_group == "Lower"]))
cat(sprintf("Wilcoxon W = %.3f, p-value = %.4g\n",
            test_result$statistic, test_result$p.value))
cat(ifelse(test_result$p.value < 0.05,
           "At alpha=0.05 the observed difference IS statistically significant.\n",
           "At alpha=0.05 the observed difference is NOT statistically significant.\n"))
cat("Interpretation: association only. This is observational data; no causal claim.\n")
