"""
Flivo Backlink Opportunity Analytics — Advanced Analytics
============================================================
No supervised ML (LogReg / Random Forest / Neural Nets / Decision Trees /
Naive Bayes / Time Series / PCA) — deliberately excluded because:

  - This is a ~105-row opportunity-scoring dataset with no labeled outcome
    variable (no "this backlink worked / didn't work" history yet), so
    supervised classification/regression models would have nothing valid
    to learn from and would just overfit noise.
  - PCA assumes many correlated numeric dimensions; here we have at most
    3-4 partially-populated numeric fields (DA, DR, Traffic, Price) with
    heavy missingness, which PCA would either force through with
    misleading imputation or reject outright.
  - Time series requires observations over time; this is a point-in-time
    research snapshot.

Unsupervised, transparent, business-interpretable methods (clustering,
weighted scoring, Pareto) are the right tool here because a founder needs
to see and defend *why* a platform ranks where it does — a black-box model
score would be less useful, not more, for an outreach decision.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from cleaning import min_max_normalize
from config import OPPORTUNITY_WEIGHTS, RANDOM_STATE, N_CLUSTERS


def validate_cluster_count(master_df: pd.DataFrame, k_range=range(2, 6)) -> pd.DataFrame:
    """
    Elbow method (inertia) + silhouette score across a range of K values,
    so the choice of N_CLUSTERS in config.py is justified rather than
    arbitrary. Run only on the subset of rows with enough real numeric
    data to cluster meaningfully (same rule as run_kmeans).
    """
    df = master_df.dropna(subset=["DA_clean"]).copy()
    feature_cols = ["DA_clean", "DR_clean", "Traffic_clean", "Price_clean"]
    for col in feature_cols:
        df[f"{col}_norm"] = min_max_normalize(df[col])
    norm_cols = [f"{c}_norm" for c in feature_cols]
    df[norm_cols] = df[norm_cols].fillna(df[norm_cols].median(numeric_only=True))

    records = []
    for k in k_range:
        if len(df) <= k:
            continue
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(df[norm_cols])
        sil = silhouette_score(df[norm_cols], labels) if len(set(labels)) > 1 else np.nan
        records.append({"k": k, "inertia": round(km.inertia_, 3), "silhouette_score": round(sil, 3)})
    return pd.DataFrame(records)


def correlation_matrix(master_df: pd.DataFrame) -> pd.DataFrame:
    """Correlation matrix over the numeric fields that actually have
    enough overlapping non-null data to be meaningful."""
    numeric_cols = ["DA_clean", "DR_clean", "Traffic_clean", "Price_clean",
                     "Guest_Post_Score", "Food_Relevance_Score"]
    return master_df[numeric_cols].corr(min_periods=5).round(2)


def run_kmeans(master_df: pd.DataFrame, n_clusters: int = N_CLUSTERS) -> pd.DataFrame:
    """K-Means over normalized DA/DR/Traffic/Price for platforms that have
    at least DA and one other numeric field populated. Rows without enough
    numeric data are left with Cluster = NaN rather than force-fit."""
    df = master_df.copy()
    feature_cols = ["DA_clean", "DR_clean", "Traffic_clean", "Price_clean"]

    usable = df.dropna(subset=["DA_clean"]).copy()
    for col in feature_cols:
        usable[f"{col}_norm"] = min_max_normalize(usable[col])
    # Fill only the *normalized* secondary features' remaining gaps with the
    # column median of normalized values (0.5-centered), documented explicitly,
    # so clustering can still run on DA-only-known rows without pretending
    # we know their DR/Traffic/Price.
    norm_cols = [f"{c}_norm" for c in feature_cols]
    usable[norm_cols] = usable[norm_cols].fillna(usable[norm_cols].median(numeric_only=True))

    if len(usable) < n_clusters:
        df["Cluster"] = np.nan
        return df

    km = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=10)
    usable["Cluster"] = km.fit_predict(usable[norm_cols])

    # Label clusters by mean DA so results are interpretable (not arbitrary 0/1/2)
    cluster_order = usable.groupby("Cluster")["DA_clean"].mean().sort_values(ascending=False).index
    label_map = {cluster_order[0]: "Premium Authority Tier",
                 cluster_order[-1]: "Budget / Lower-Verified Tier"}
    if n_clusters == 3:
        label_map[cluster_order[1]] = "Mid-Tier"
    usable["Cluster_Label"] = usable["Cluster"].map(label_map)

    df = df.merge(usable[["Cluster", "Cluster_Label"]], left_index=True, right_index=True, how="left")
    return df


def compute_opportunity_score(master_df: pd.DataFrame) -> pd.DataFrame:
    """
    Weighted Opportunity Score (documented handling of missing data):

      30% Domain Authority   10% Guest-Post Availability
      20% Domain Rating       5% Cost Efficiency (free/cheap scores higher)
      20% Monthly Traffic
      15% Food Relevance

    Missing-value rule: each component is normalized 0-1 using only the
    platforms that HAVE that metric. If a platform is missing a component,
    that weight is proportionally redistributed across the components the
    platform DOES have (rather than treating missing as zero, which would
    unfairly punish a genuinely strong but unverified platform, or filling
    with a guessed value, which this project's data policy prohibits).
    Every scored row is flagged with `Partial_Data=True` when any component
    was missing, so a high rank is never silently built on assumptions.
    """
    df = master_df.copy()

    df["DA_norm"] = min_max_normalize(df["DA_clean"])
    df["DR_norm"] = min_max_normalize(df["DR_clean"])
    df["Traffic_norm"] = min_max_normalize(df["Traffic_clean"])
    df["Food_norm"] = df["Food_Relevance_Score"]  # already 0-1
    df["GuestPost_norm"] = df["Guest_Post_Score"]  # already 0-1
    # Cost efficiency: free = 1.0; paid = inverse-normalized price (cheaper = higher score)
    price_norm = min_max_normalize(df["Price_clean"])
    df["Cost_norm"] = df.apply(
        lambda r: 1.0 if r["Free_Paid"] == "Free" else (
            1 - price_norm[r.name] if pd.notna(price_norm[r.name]) else np.nan
        ), axis=1
    )

    component_cols = {
        "DA": "DA_norm", "DR": "DR_norm", "Traffic": "Traffic_norm",
        "Food_Relevance": "Food_norm", "Guest_Post": "GuestPost_norm", "Cost_Efficiency": "Cost_norm",
    }

    # --- Eligibility threshold (critical fix) ---
    # Naively redistributing weight across only the components a row HAS
    # rewards sparse data: a platform with only Food_Relevance=1 and
    # Cost=1 (free) known would score a perfect 1.0 despite having zero
    # authority/traffic evidence — outranking fully-verified platforms.
    # To prevent that artifact, a row is only eligible for a comparable
    # Opportunity Score if:
    #   (a) DA is known (DA carries the largest single weight, 30%), AND
    #   (b) at least half of the 6 components (>=3) are known.
    # Rows failing this are scored as NaN and routed to a separate
    # "Insufficient Data — Needs Manual Verification" list instead of
    # being silently ranked on partial information.
    MIN_COMPONENTS_REQUIRED = 3

    scores, partial_flags, n_components_used, eligible_flags = [], [], [], []
    for _, row in df.iterrows():
        weighted_sum, weight_used, n_present = 0.0, 0.0, 0
        for key, col in component_cols.items():
            val = row[col]
            if pd.notna(val):
                weighted_sum += OPPORTUNITY_WEIGHTS[key] * val
                weight_used += OPPORTUNITY_WEIGHTS[key]
                n_present += 1

        da_known = pd.notna(row["DA_norm"])
        eligible = da_known and n_present >= MIN_COMPONENTS_REQUIRED

        if eligible:
            # Rescale by weight actually available so scores stay 0-1 comparable
            # ONLY among rows that clear the eligibility bar above.
            scores.append(round(weighted_sum / weight_used, 4))
        else:
            scores.append(np.nan)

        eligible_flags.append(eligible)
        partial_flags.append(n_present < len(component_cols))
        n_components_used.append(n_present)

    df["Opportunity_Score"] = scores
    df["Score_Eligible"] = eligible_flags
    df["Partial_Data"] = partial_flags
    df["N_Components_Used"] = n_components_used
    return df


def pareto_table(scored_df: pd.DataFrame) -> pd.DataFrame:
    """Ranked table with cumulative % of total opportunity score — the
    numeric backbone behind the Pareto chart."""
    valid = scored_df.dropna(subset=["Opportunity_Score"]).sort_values(
        "Opportunity_Score", ascending=False).reset_index(drop=True)
    valid["Cumulative_Pct"] = round(100 * valid["Opportunity_Score"].cumsum() / valid["Opportunity_Score"].sum(), 1)
    valid["Rank"] = valid.index + 1
    return valid[["Rank", "Name", "Sheet", "Opportunity_Score", "Cumulative_Pct", "Partial_Data"]]


def quick_wins_and_long_term(scored_df: pd.DataFrame, score_threshold: float = 0.55) -> tuple:
    """
    Quick Wins: high score, free, guest post readily available -> act this month.
    Long-Term Opportunities: high score, paid or harder approval -> plan/budget for later.
    """
    valid = scored_df.dropna(subset=["Opportunity_Score"])

    quick_wins = valid[
        (valid["Opportunity_Score"] >= score_threshold) &
        (valid["Free_Paid"] == "Free") &
        (valid["Guest_Post_Score"].fillna(0) >= 0.5)
    ].sort_values("Opportunity_Score", ascending=False)

    long_term = valid[
        (valid["Opportunity_Score"] >= score_threshold) &
        (valid["Free_Paid"] != "Free")
    ].sort_values("Opportunity_Score", ascending=False)

    cols = ["Name", "Sheet", "Opportunity_Score", "Free_Paid", "Price_clean", "Partial_Data"]
    return quick_wins[cols], long_term[cols]


def budget_optimization(scored_df: pd.DataFrame, monthly_budget_usd: float = 500) -> pd.DataFrame:
    """Greedy budget allocation: fill the monthly budget with the highest
    Opportunity-Score-per-dollar paid platforms first."""
    paid = scored_df.dropna(subset=["Opportunity_Score", "Price_clean"])
    paid = paid[paid["Price_clean"] > 0].copy()
    paid["Score_per_Dollar"] = paid["Opportunity_Score"] / paid["Price_clean"]
    paid = paid.sort_values("Score_per_Dollar", ascending=False)

    selected, running_total = [], 0.0
    for _, row in paid.iterrows():
        if running_total + row["Price_clean"] <= monthly_budget_usd:
            selected.append(row)
            running_total += row["Price_clean"]
    result = pd.DataFrame(selected)[["Name", "Sheet", "Price_clean", "Opportunity_Score", "Score_per_Dollar"]] \
        if selected else pd.DataFrame(columns=["Name", "Sheet", "Price_clean", "Opportunity_Score", "Score_per_Dollar"])
    result.attrs["budget"] = monthly_budget_usd
    result.attrs["spent"] = round(running_total, 2)
    result.attrs["remaining"] = round(monthly_budget_usd - running_total, 2)
    return result
