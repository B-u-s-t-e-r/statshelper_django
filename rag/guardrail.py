from dataclasses import dataclass
from typing import Optional


# ── Covered topic vocabulary ───────────────────────────────────────────────
# All meaningful statistical terms covered by current KB
COVERED_VOCABULARY = {
    # Hypothesis Testing
    "t-test", "ttest", "t test", "anova", "chi-square", "chi square",
    "fisher", "levene", "shapiro", "wilcoxon", "mann-whitney", "mann whitney",
    "kruskal", "kruskal-wallis", "welch", "paired", "independent",
    "hypothesis", "null hypothesis", "alternative hypothesis", "p-value",
    "p value", "significance", "significant", "alpha", "reject",

    # Regression & Correlation
    "regression", "correlation", "pearson", "spearman", "logistic",
    "linear regression", "predict", "prediction", "forecast",
    "dependent variable", "independent variable", "coefficient",
    "r-squared", "r squared",

    # Non-Parametric
    "non-parametric", "nonparametric", "ordinal", "rank", "ranks",
    "median", "non parametric",

    # Distributions & Probability
    "normal distribution", "gaussian", "bell curve", "bayes", "bayesian",
    "prior", "posterior", "probability", "distribution", "clt",
    "central limit", "standard deviation", "variance", "mean",

    # Foundations
    "descriptive statistics", "descriptive", "summarize", "summary",
    "effect size", "cohen", "confidence interval", "margin of error",
    "type 1 error", "type 2 error", "type i", "type ii", "false positive",
    "false negative", "power", "sample size", "normality",

    # Common user phrasings
    "compare groups", "compare means", "group difference",
    "two groups", "three groups", "multiple groups",
    "before after", "pre post", "same subjects",
    "categorical", "continuous", "binary", "ordinal",
    "skewed", "outliers", "not normal", "assumption",
    "association", "relationship", "trend"
}

# Topics explicitly NOT covered — trigger out-of-scope
OUT_OF_SCOPE_SIGNALS = {
    # Phase 2 / advanced (not yet in KB)
    "sample size calculation", "calculate sample size", "determine sample size",
    "how many samples", "how many participants", "power analysis", "bonferroni",
    "multiple testing", "false discovery", "fdr",
    "two-way anova", "two way anova", "repeated measures",
    "mixed model", "multilevel", "hierarchical",
    "time series", "arima", "autocorrelation", "stationarity",
    "polynomial regression", "ridge", "lasso", "elastic net",
    "random forest", "decision tree", "neural network", "deep learning",
    "svm", "support vector", "clustering", "k-means", "pca",
    "principal component", "factor analysis", "survival analysis",
    "cox regression", "kaplan meier", "hazard",
    "structural equation", "sem", "path analysis",
    "meta-analysis", "systematic review",
    "kendall", "kendall tau", "cramers v",
    "binomial distribution", "poisson distribution",
    "negative binomial", "gamma distribution",
    "bootstrap", "permutation test", "monte carlo",
    "cross validation", "overfitting", "regularization",
    "confusion matrix", "roc curve", "auc",
    "residual analysis", "heteroscedasticity test",
    "durbin watson", "vif", "multicollinearity check"
}

# Minimum confidence threshold — below this triggers guardrail
CONFIDENCE_THRESHOLD = 45.0

# Covered concept list for display
COVERED_CONCEPTS = [
    # Hypothesis Testing
    ("Hypothesis Testing", [
        "Independent Samples t-Test",
        "Welch's t-Test (unequal variances)",
        "Paired Samples t-Test",
        "One Sample t-Test",
        "One-Way ANOVA",
        "Chi-Square Test of Independence",
        "Bayes' Theorem",
    ]),
    # Non-Parametric
    ("Non-Parametric Tests", [
        "Mann-Whitney U Test",
        "Wilcoxon Signed-Rank Test",
        "Kruskal-Wallis Test",
        "Fisher's Exact Test",
    ]),
    # Assumption Testing
    ("Assumption Checks", [
        "Shapiro-Wilk Normality Test",
        "Levene's Test for Equal Variances",
    ]),
    # Regression & Correlation
    ("Regression & Correlation", [
        "Pearson Correlation",
        "Spearman Rank Correlation",
        "Simple Linear Regression",
        "Multiple Linear Regression",
        "Logistic Regression",
    ]),
    # Foundations
    ("Statistical Foundations", [
        "Descriptive Statistics",
        "Normal Distribution",
        "Central Limit Theorem",
        "Confidence Intervals",
        "Hypothesis Testing Framework",
        "Type I and Type II Errors",
        "Effect Size",
    ]),
]


@dataclass
class GuardrailResult:
    is_in_scope: bool
    reason: str                        # why in/out of scope
    confidence: float                  # 0-100
    closest_concept: Optional[str]     # best guess if out of scope
    out_of_scope_signal: Optional[str] # which term triggered rejection
    message: Optional[str]             # message to show user if out of scope


def check_scope(query: str, retrieval_confidence: float = 100.0,
                closest_concept: str = None) -> GuardrailResult:
    """
    Two-layer guardrail check.

    Layer 1: Keyword-based — fast pre-retrieval check
    Layer 2: Confidence-based — post-retrieval check

    Returns GuardrailResult with is_in_scope flag and message.
    """
    q = query.lower().strip()

    # ── Layer 1a: Explicit out-of-scope signal detection ──────────────
    for signal in OUT_OF_SCOPE_SIGNALS:
        if signal in q:
            return GuardrailResult(
                is_in_scope=False,
                reason=f"Query contains topic not yet in knowledge base: '{signal}'",
                confidence=0.0,
                closest_concept=closest_concept,
                out_of_scope_signal=signal,
                message=_build_message(query, closest_concept, signal)
            )

    # ── Layer 1b: Check if query has ANY covered vocabulary ───────────
    query_words = set(q.replace("-", " ").split())
    multi_word_matches = sum(1 for term in COVERED_VOCABULARY if term in q)
    single_word_matches = sum(1 for word in query_words if word in COVERED_VOCABULARY)
    total_matches = multi_word_matches + single_word_matches

    # Very short queries with no statistical vocabulary
    meaningful_words = [w for w in query_words
                        if len(w) > 3 and w not in
                        {"what","does","should","would","could","have",
                         "this","that","with","from","want","need","help",
                         "tell","give","show","explain","how","why","when",
                         "which","where","will","about","using","after",
                         "before","between","into","than","more","some"}]

    if len(meaningful_words) > 0 and total_matches == 0:
        return GuardrailResult(
            is_in_scope=False,
            reason="No statistical vocabulary found in query",
            confidence=0.0,
            closest_concept=closest_concept,
            out_of_scope_signal=None,
            message=_build_message(query, closest_concept, None)
        )

    # ── Layer 2: Post-retrieval confidence check ──────────────────────
    if retrieval_confidence < CONFIDENCE_THRESHOLD:
        return GuardrailResult(
            is_in_scope=False,
            reason=f"Retrieval confidence too low: {retrieval_confidence:.1f}% < {CONFIDENCE_THRESHOLD}%",
            confidence=retrieval_confidence,
            closest_concept=closest_concept,
            out_of_scope_signal=None,
            message=_build_message(query, closest_concept, None)
        )

    # ── In scope ──────────────────────────────────────────────────────
    return GuardrailResult(
        is_in_scope=True,
        reason="Query matches covered statistical topics",
        confidence=retrieval_confidence,
        closest_concept=closest_concept,
        out_of_scope_signal=None,
        message=None
    )


def _build_message(query: str, closest_concept: str,
                   signal: str) -> str:
    """Build the user-facing out-of-scope message."""
    lines = []
    lines.append("⚠️ This question appears to be outside my current knowledge base.")
    lines.append("")

    if signal:
        lines.append(f"📌 Topic detected: **{signal}** — not yet covered.")
    else:
        lines.append("📌 I could not find a strong match in my knowledge base for this query.")

    if closest_concept:
        lines.append("")
        lines.append(f"💡 Closest available topic: **{closest_concept}**")
        lines.append("   This may partially address your question.")

    lines.append("")
    lines.append("📚 **Topics I currently cover:**")

    for category, concepts in COVERED_CONCEPTS:
        lines.append(f"\n**{category}**")
        for concept in concepts:
            lines.append(f"  • {concept}")

    lines.append("")
    lines.append("🔄 **Suggestions:**")
    lines.append("  • Try rephrasing using the concept names listed above")
    lines.append("  • Ask about a related concept that IS covered")
    lines.append("  • This topic is planned for a future KB update")

    return "\n".join(lines)


def get_covered_topics_text() -> str:
    """Return a plain text list of all covered topics for display."""
    lines = ["📚 Currently Covered Statistical Concepts\n"]
    for category, concepts in COVERED_CONCEPTS:
        lines.append(f"\n{category}:")
        for concept in concepts:
            lines.append(f"  • {concept}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Test the guardrail
    test_queries = [
        # Should be IN scope
        ("compare two group means",                      True),
        ("my data is not normal two groups",             True),
        ("what is p-value",                              True),
        ("pearson correlation formula",                  True),
        # Should be OUT of scope
        ("how to calculate sample size for my study",    False),
        ("I ran 10 tests should I use bonferroni",       False),
        ("build a random forest classifier",             False),
        ("run pca on my dataset",                        False),
        ("time series forecasting with arima",           False),
        ("what is the weather today",                    False),
    ]

    print("Guardrail Tests")
    print("=" * 60)
    passed = 0
    for query, expected_in_scope in test_queries:
        result = check_scope(query)
        ok = result.is_in_scope == expected_in_scope
        if ok:
            passed += 1
        status = "✓" if ok else "✗"
        scope = "IN " if result.is_in_scope else "OUT"
        print(f"{status} [{scope}] {query}")
        if not ok:
            print(f"      Reason: {result.reason}")

    print(f"\n{passed}/{len(test_queries)} passed")