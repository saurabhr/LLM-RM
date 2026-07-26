# exp2_clm_confidence.R
# Cumulative Link Model (CLM) for Experiment 2 confidence ratings
# Fixed-effects ordinal regression via ordinal::clm()
# Run with: Rscript exp2_clm_confidence.R

suppressPackageStartupMessages({
  library(ordinal)
  library(emmeans)
  library(car)
})

cat("R version:", paste(R.version$major, R.version$minor, sep="."), "\n")
cat("ordinal version:", as.character(packageVersion("ordinal")), "\n\n")

# ── Paths ──────────────────────────────────────────────────────────────────
script_dir <- tryCatch({
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg) > 0) dirname(normalizePath(sub("^--file=", "", file_arg)))
  else getwd()
}, error = function(e) getwd())
PROJ      <- normalizePath(file.path(script_dir, "..", ".."))
DATA_FILE <- file.path(PROJ, "data", "processed", "exp2_trial_data.csv")
LOG_FILE  <- file.path(PROJ, "reports", "logs", "exp2_clm_confidence_out.txt")
dir.create(dirname(LOG_FILE), recursive = TRUE, showWarnings = FALSE)

cat("Data:", DATA_FILE, "\n")
cat("Log :", LOG_FILE, "\n\n")

# ── Load & prepare data ────────────────────────────────────────────────────
cat("Loading data...\n")
df <- read.csv(DATA_FILE, stringsAsFactors = FALSE)
cat("N =", nrow(df), "\n\n")

df$confidence_ord        <- factor(df$confidence, levels = 1:6, ordered = TRUE)
df$source                <- factor(sub("test:", "", df$source_test),
                                   levels = c("perceived", "imagined"))
df$setsize               <- factor(as.character(df$setsize), levels = c("20", "40"))
df$fb_exp                <- factor(as.character(df$fb_exp),  levels = c("False", "True"))
df$model                 <- factor(df$model,
    levels = c("Gemma3:12b","Gemma3:12b-QAT","Gemma3:27b",
               "Gemma3:27b-QAT","Llama3.3:70b","Llama4:16x17b"))
df$accuracy              <- factor(df$accuracy, levels = c(0, 1))
df$reading_hallucination <- factor(df$reading_hallucination, levels = c(0, 1))
df$rating_cen            <- df$rating - mean(df$rating, na.rm = TRUE)
df$order_c               <- df$order - 1L

cat("Reference levels:\n")
cat("  source  :", levels(df$source)[1], "\n")
cat("  setsize :", levels(df$setsize)[1], "\n")
cat("  fb_exp  :", levels(df$fb_exp)[1], "\n")
cat("  model   :", levels(df$model)[1], "\n")
cat("  accuracy:", levels(df$accuracy)[1], "\n\n")
cat("Confidence distribution:\n"); print(table(df$confidence_ord)); cat("\n")

# ── Fit CLM model sequence ─────────────────────────────────────────────────
cat("Fitting null model...\n")
t0 <- proc.time()
m0 <- clm(confidence_ord ~ 1, data = df, link = "logit")
cat("  Done in", round((proc.time()-t0)[3], 2), "s\n\n")

cat("Fitting additive model...\n")
t0 <- proc.time()
m_add <- clm(confidence_ord ~
    source + setsize + fb_exp + model +
    accuracy + reading_hallucination + rating_cen + order_c,
    data = df, link = "logit")
cat("  Done in", round((proc.time()-t0)[3], 2), "s\n\n")

cat("Fitting interactive model...\n")
t0 <- proc.time()
m_int <- clm(confidence_ord ~
    source * setsize + source * fb_exp + setsize * fb_exp +
    model + accuracy + reading_hallucination + rating_cen + order_c,
    data = df, link = "logit")
cat("  Done in", round((proc.time()-t0)[3], 2), "s\n\n")

cat("All three models fitted.\n\n")

# ── Write full output to log ───────────────────────────────────────────────
cat("Writing log to:", LOG_FILE, "\n")
sink(LOG_FILE)

cat("=== Experiment 2: CLM for Confidence Ratings ===\n")
cat("N =", nrow(df), "observations\n")
cat("Model: clm(confidence_ord ~ source*setsize + source*fb_exp + setsize*fb_exp +\n")
cat("           model + accuracy + reading_hallucination + rating_cen + order_c,\n")
cat("           link='logit')\n\n")

cat("=== Model Comparisons (LRT) ===\n")
lrt <- anova(m0, m_add, m_int)
print(lrt)

cat("\n=== Interactive Model Summary ===\n")
print(summary(m_int))

cat("\n=== Type-II Wald Chi-Square Tests ===\n")
wald <- car::Anova(m_int, type = "II")
print(wald)

cat("\n=== OR Table (Interactive Model) ===\n")
coefs     <- coef(summary(m_int))
is_thresh <- grepl("[|]", rownames(coefs))
pred_rows <- coefs[!is_thresh, , drop = FALSE]
ci        <- confint(m_int, level = 0.95)
ci_pred   <- ci[!grepl("[|]", rownames(ci)), , drop = FALSE]

or_table <- data.frame(
  b     = round(pred_rows[, "Estimate"],   4),
  SE    = round(pred_rows[, "Std. Error"], 4),
  z     = round(pred_rows[, "z value"],    4),
  p     = round(pred_rows[, "Pr(>|z|)"],  4),
  OR    = round(exp(pred_rows[, "Estimate"]), 4),
  OR_lo = round(exp(ci_pred[, 1]),         4),
  OR_hi = round(exp(ci_pred[, 2]),         4)
)
or_table$sig <- ifelse(or_table$p < .001, "***",
               ifelse(or_table$p < .01,  "**",
               ifelse(or_table$p < .05,  "*", "")))
print(or_table)

cat("\n=== Pseudo-R² ===\n")
ll0    <- as.numeric(logLik(m0))
ll_int <- as.numeric(logLik(m_int))
n      <- nrow(df)
mcfadden   <- 1 - ll_int / ll0
nagelkerke <- (1 - exp(-2/n * (ll_int - ll0))) /
              (1 - exp( 2/n * ll0))
cat(sprintf("McFadden  R2  = %.4f\n", mcfadden))
cat(sprintf("Nagelkerke R2 = %.4f\n", nagelkerke))
cat(sprintf("AIC null        = %.1f\n", AIC(m0)))
cat(sprintf("AIC additive    = %.1f\n", AIC(m_add)))
cat(sprintf("AIC interactive = %.1f\n", AIC(m_int)))

cat("\n=== Post-hoc: Source x Feedback (Bonferroni) ===\n")
emm_sfb <- emmeans(m_int, ~ source * fb_exp, mode = "mean.class")
print(summary(pairs(emm_sfb, adjust = "bonferroni")))

cat("\n=== Post-hoc: Source x Set Size (Bonferroni) ===\n")
emm_sss <- emmeans(m_int, ~ source * setsize, mode = "mean.class")
print(summary(pairs(emm_sss, adjust = "bonferroni")))

cat("\n=== APA-style Table ===\n")
cat(sprintf("%-45s %8s %8s %8s %8s %8s  %s\n",
    "Term", "b", "SE", "z", "p", "OR", "95% CI"))
cat(strrep("-", 105), "\n")
for (i in seq_len(nrow(pred_rows))) {
  b  <- pred_rows[i, "Estimate"]
  se <- pred_rows[i, "Std. Error"]
  z  <- pred_rows[i, "z value"]
  p  <- pred_rows[i, "Pr(>|z|)"]
  or <- exp(b)
  lo <- exp(ci_pred[i, 1])
  hi <- exp(ci_pred[i, 2])
  sig <- ifelse(p < .001, "***", ifelse(p < .01, "**", ifelse(p < .05, "*", "")))
  cat(sprintf("%-45s %8.3f %8.3f %8.3f %8s %8.3f [%.3f, %.3f] %s\n",
    rownames(pred_rows)[i], b, se, z,
    ifelse(p < .001, "< .001", sprintf("%.3f", p)),
    or, lo, hi, sig))
}
cat("\nNote. CLM = Cumulative Link Model (logit link, fixed effects).\n")
cat("OR = odds ratio; 95% CI = profile likelihood CI.\n")
cat("Reference: source = perceived, setsize = 20, fb_exp = False,\n")
cat("           model = Gemma3:12b, accuracy = 0 (incorrect),\n")
cat("           reading_hallucination = 0.\n")

sink()
cat("Done. Log written to:", LOG_FILE, "\n")
