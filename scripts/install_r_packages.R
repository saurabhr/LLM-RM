# =============================================================================
# install_r_packages.R
# Installs all R packages needed for the Experiment 2 mixed-model analysis.
# Run via:  Rscript install_r_packages.R
#
# Packages installed
# ------------------
#   lme4       — linear/generalised mixed-effects models
#   lmerTest   — Satterthwaite df + p-values for lmer output
#   emmeans    — estimated marginal means + pairwise contrasts
#   DHARMa     — residual diagnostics for hierarchical models (GLMM)
#   car        — VIF (vif()) + Anova() type-III tests
#   Matrix     — sparse matrix support (lme4 dependency, pin version)
#   pbkrtest   — Kenward-Roger F-tests (optional, used by emmeans)
#   optimx     — extended optimizer suite (nloptwrap lives here)
# =============================================================================

required <- c(
  "lme4",
  "lmerTest",
  "emmeans",
  "DHARMa",
  "car",
  "Matrix",
  "pbkrtest",
  "optimx"
)

cat("Installing R packages...\n\n")

for (pkg in required) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    cat(sprintf("  Installing %-12s ...\n", pkg))
    install.packages(
      pkg,
      repos        = "https://cloud.r-project.org",
      quiet        = TRUE,
      dependencies = TRUE
    )
  } else {
    installed_ver <- as.character(packageVersion(pkg))
    cat(sprintf("  ✓  %-12s  %s  (already installed)\n", pkg, installed_ver))
  }
}

cat("\n── Verification ──\n")
all_ok <- TRUE
for (pkg in required) {
  if (requireNamespace(pkg, quietly = TRUE)) {
    cat(sprintf("  ✓  %-12s  %s\n", pkg, as.character(packageVersion(pkg))))
  } else {
    cat(sprintf("  ✗  %-12s  FAILED\n", pkg))
    all_ok <- FALSE
  }
}

if (all_ok) {
  cat("\nAll R packages installed successfully.\n")
} else {
  cat("\nSome packages failed — check CRAN availability and re-run.\n")
  quit(status = 1)
}
