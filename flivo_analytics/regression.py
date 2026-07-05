"""
Flivo Backlink Opportunity Analytics — Regression Analysis
=============================================================
IMPORTANT DISTINCTION FROM THE EXCLUDED ML METHODS:

The project brief excludes Logistic Regression, Random Forest, Neural
Networks, Decision Trees, Naive Bayes, Time Series, and PCA because this
dataset has no labeled outcome to PREDICT (there is no historical record
of "this backlink worked / didn't work" to train a classifier on), and
too few, too sparsely populated numeric fields for PCA to be meaningful.

Simple Linear Regression is used here differently: not to predict an
unknown outcome, but to QUANTIFY THE STRENGTH OF AN OBSERVED RELATIONSHIP
between two already-known, fully-real variables (e.g. does higher Domain
Authority tend to come with higher Traffic, among the platforms where
both are verified?). This is descriptive/exploratory regression — it
produces an R^2 and a slope, not a prediction for a new unseen platform.
It is run ONLY on the subset of rows where both variables are genuinely
known (never on imputed or guessed values), and the sample size is always
reported alongside the result so a small-n regression is never
overstated as a confident finding.
"""
import numpy as np
import pandas as pd
from scipy import stats


def simple_linear_regression(master_df: pd.DataFrame, x_col: str, y_col: str) -> dict:
    """
    Fit y = slope * x + intercept using ordinary least squares, restricted
    to rows where both x_col and y_col are non-null. Returns slope,
    intercept, R^2, correlation, p-value, and sample size — with an
    explicit `reliable` flag (n >= 10) since regression on very small
    samples is not a trustworthy basis for a business claim.
    """
    paired = master_df[[x_col, y_col]].dropna()
    n = len(paired)

    if n < 3:
        return {
            "x": x_col, "y": y_col, "n": n, "reliable": False,
            "note": f"Only {n} platforms have both {x_col} and {y_col} known — "
                    "too few to fit any regression line meaningfully."
        }

    slope, intercept, r_value, p_value, std_err = stats.linregress(paired[x_col], paired[y_col])

    return {
        "x": x_col, "y": y_col, "n": n,
        "slope": round(slope, 4),
        "intercept": round(intercept, 2),
        "r_squared": round(r_value ** 2, 3),
        "correlation": round(r_value, 3),
        "p_value": round(p_value, 4),
        "reliable": n >= 10,
        "note": (f"Based on only {n} platforms — directional signal, not a confident "
                 "statistical finding." if n < 10 else
                 f"Based on {n} platforms with both metrics verified — reasonable sample for "
                 "a descriptive trend, though still not large enough for predictive use."),
    }


def run_all_regressions(master_df: pd.DataFrame) -> pd.DataFrame:
    """Run the business-relevant regression pairs and return a tidy summary table."""
    pairs = [
        ("DA_clean", "Traffic_clean"),   # Does higher authority track with higher traffic?
        ("DA_clean", "DR_clean"),        # Do DA and DR (two different authority metrics) agree?
        ("DR_clean", "Traffic_clean"),   # Cross-check: does DR also track with traffic?
    ]
    records = []
    for x, y in pairs:
        result = simple_linear_regression(master_df, x, y)
        records.append(result)
    return pd.DataFrame(records)


def interpret_regression(result: dict) -> str:
    """Plain-language interpretation for the written report."""
    if not result.get("reliable") and result.get("n", 0) < 3:
        return result["note"]

    r2 = result.get("r_squared", np.nan)
    if pd.isna(r2):
        return "Not enough data to interpret."

    strength = "strong" if r2 >= 0.6 else "moderate" if r2 >= 0.3 else "weak"
    direction = "positive" if result["slope"] > 0 else "negative"
    return (f"{result['x']} explains about {r2*100:.0f}% of the variation in {result['y']} "
            f"among the {result['n']} platforms where both are known (R²={r2}, {strength} "
            f"{direction} relationship). {result['note']}")
