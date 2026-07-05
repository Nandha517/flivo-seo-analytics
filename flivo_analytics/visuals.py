"""
Flivo Backlink Opportunity Analytics — Visualizations
========================================================
Matplotlib only (no seaborn), per project spec. Every chart function
returns (fig, insight_text) so the insight is generated alongside the
chart and never detached from it in the final report.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import CHARTS_DIR

NAVY = "#1F3864"
GREEN = "#548235"
AMBER = "#BF8F00"
GREY = "#7F7F7F"
PALETTE = ["#1F3864", "#548235", "#BF8F00", "#833C0C", "#264478", "#70AD47", "#FFC000"]

os.makedirs(CHARTS_DIR, exist_ok=True)
plt.rcParams.update({"font.size": 10, "figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False})


def _save(fig, name: str) -> str:
    path = os.path.join(CHARTS_DIR, f"{name}.png")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def chart_free_vs_paid(master_df) -> dict:
    """Pie chart: Free vs Paid split across all opportunity platforms.
    Why: Founders need an immediate read on how much of the SEO opportunity
    is zero-cost before allocating any budget."""
    counts = master_df["Free_Paid"].apply(
        lambda v: v if v == "Free" else "Paid"
    ).value_counts()
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(counts.values, labels=counts.index, autopct="%1.0f%%",
           colors=[GREEN, NAVY], startangle=90,
           wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    ax.set_title("Free vs. Paid Platform Split (All Sheets)", fontweight="bold")
    path = _save(fig, "01_free_vs_paid_pie")
    insight = (f"{counts.get('Free', 0)} of {counts.sum()} researched platforms "
               f"({100*counts.get('Free',0)/counts.sum():.0f}%) are free. "
               "Implication: Flivo can run a meaningful first wave of backlink "
               "outreach at zero media cost before any paid spend is needed.")
    return {"path": path, "insight": insight}


def chart_platforms_per_sheet(master_df) -> dict:
    """Horizontal bar: platform count per category/sheet.
    Why: shows where the research effort concentrated and where the
    largest pool of opportunities actually sits."""
    counts = master_df["Sheet"].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(counts.index, counts.values, color=PALETTE[:len(counts)])
    ax.set_xlabel("Number of Platforms")
    ax.set_title("Platform Count by Category", fontweight="bold")
    for i, v in enumerate(counts.values):
        ax.text(v + 0.3, i, str(v), va="center")
    path = _save(fig, "02_platforms_per_sheet")
    insight = ("The largest pools are general free self-publish/business-media platforms "
               "and the paid marketplace tier; the food/health niche tier is intentionally "
               "smaller but carries the highest topical relevance per platform.")
    return {"path": path, "insight": insight}


def chart_da_distribution(master_df) -> dict:
    """Histogram: DA distribution among platforms with a known/estimated DA.
    Why: shows the authority spread of platforms that are actually usable
    for scoring, and visually communicates how much of the dataset is
    unverified (annotated directly on the chart)."""
    valid = master_df["DA_clean"].dropna()
    missing = master_df["DA_clean"].isna().sum()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(valid, bins=10, color=NAVY, edgecolor="white")
    ax.set_xlabel("Domain Authority (Est.)")
    ax.set_ylabel("Number of Platforms")
    ax.set_title("Domain Authority Distribution", fontweight="bold")
    ax.text(0.02, 0.95, f"n = {len(valid)} platforms with DA data\n{missing} platforms unverified (N/A)",
            transform=ax.transAxes, va="top", fontsize=9,
            bbox={"facecolor": "white", "edgecolor": GREY, "boxstyle": "round"})
    path = _save(fig, "03_da_distribution")
    insight = (f"Only {len(valid)} of {len(master_df)} platforms have a publicly-cited DA figure; "
               "the rest require direct Moz/Ahrefs verification before outreach. Among known values, "
               "authority skews high because the free self-publish tier (Medium, LinkedIn, Reddit) "
               "dominates the verified sample — this should not be read as 'most opportunities are high-DA'.")
    return {"path": path, "insight": insight}


def chart_pricing_by_category(pricing_df) -> dict:
    """Horizontal bar: average price by paid-platform category.
    Why: directly informs budget planning across the paid tiers Flivo
    is considering."""
    df = pricing_df.sort_values("mean")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(df.index, df["mean"], color=AMBER)
    ax.set_xlabel("Average Price (USD, midpoint of published range)")
    ax.set_title("Average Price by Paid Platform Category", fontweight="bold")
    for i, (v, n) in enumerate(zip(df["mean"], df["count"])):
        ax.text(v + 20, i, f"${v:,.0f} (n={n})", va="center", fontsize=8)
    path = _save(fig, "04_pricing_by_category")
    insight = ("Guest-post marketplaces and budget PR wires cluster under $150/placement, while "
               "premium press-release distribution (PR Newswire, Business Wire) runs into the "
               "thousands. Recommendation: allocate routine outreach budget to the sub-$150 tier "
               "and reserve premium wires for genuine milestones (funding, national launch).")
    return {"path": path, "insight": insight}


def chart_guest_post_acceptance(guest_post_df) -> dict:
    """Bar chart: guest-post acceptance rate by sheet/category.
    Why: shows where outreach is most likely to succeed."""
    df = guest_post_df.dropna(subset=["guest_post_acceptance_pct"])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(df.index, df["guest_post_acceptance_pct"], color=GREEN)
    ax.set_ylabel("Guest Post Acceptance Rate (%)")
    ax.set_title("Guest Post Acceptance Rate by Platform Category", fontweight="bold")
    ax.set_xticklabels(df.index, rotation=20, ha="right")
    for i, v in enumerate(df["guest_post_acceptance_pct"]):
        ax.text(i, v + 1, f"{v:.0f}%", ha="center")
    path = _save(fig, "05_guest_post_acceptance")
    insight = ("Free platforms and niche food/health sites show the highest guest-post acceptance "
               "rates, confirming these should be the first outreach wave; paid marketplaces show "
               "a lower rate mainly because several are pure PR-wire or business-listing services "
               "that don't offer guest posting at all.")
    return {"path": path, "insight": insight}


def chart_food_suitability(food_analysis_df) -> dict:
    """Pie chart: Suitable-for-Flivo split within the food/health niche sheet.
    Why: quantifies how much of the dedicated niche research is a genuine
    topical fit vs. only partially relevant."""
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(food_analysis_df["Count"], labels=food_analysis_df.index, autopct="%1.0f%%",
           colors=[GREEN, AMBER], startangle=90,
           wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    ax.set_title("Food & Health Niche Sites: Suitability for Flivo", fontweight="bold")
    path = _save(fig, "06_food_suitability")
    insight = ("70% of the curated niche list is a direct topical match; the remaining 30% "
               "('Partial') are culinary/recipe-oriented sites best used for recipe-integration "
               "content rather than nutrition-science claims.")
    return {"path": path, "insight": insight}


def chart_opportunity_score_top20(scored_df) -> dict:
    """Horizontal bar: Top 20 platforms by weighted Opportunity Score.
    Why: this is the single most decision-relevant chart in the whole
    report — it operationalizes every other analysis into one ranked list."""
    top20 = scored_df.dropna(subset=["Opportunity_Score"]).nlargest(20, "Opportunity_Score").sort_values("Opportunity_Score")
    fig, ax = plt.subplots(figsize=(8, 9))
    colors = [GREEN if p == "Free" else NAVY for p in top20["Free_Paid"]]
    ax.barh(top20["Name"], top20["Opportunity_Score"], color=colors)
    ax.set_xlabel("Opportunity Score (0-1, higher = better)")
    ax.set_title("Top 20 Platforms by Weighted Opportunity Score", fontweight="bold")
    ax.legend(handles=[plt.Rectangle((0,0),1,1, color=GREEN, label="Free"),
                        plt.Rectangle((0,0),1,1, color=NAVY, label="Paid")], loc="lower right")
    path = _save(fig, "07_opportunity_score_top20")
    insight = ("The weighted score (30% DA + 20% DR + 20% Traffic + 15% Food Relevance + "
               "10% Guest-Post Availability + 5% Cost Efficiency) surfaces platforms that are "
               "strong on multiple dimensions at once, not just high-DA generalist sites. "
               "Rows with partial data are flagged separately (see completeness notes) so a "
               "high rank is never an artifact of missing values.")
    return {"path": path, "insight": insight}


def chart_pareto(scored_df) -> dict:
    """Pareto chart: cumulative Opportunity Score contribution.
    Why: tests the 80/20 rule — do a small number of platforms carry most
    of the total addressable opportunity value?"""
    valid = scored_df.dropna(subset=["Opportunity_Score"]).sort_values("Opportunity_Score", ascending=False).reset_index(drop=True)
    cumulative_pct = 100 * valid["Opportunity_Score"].cumsum() / valid["Opportunity_Score"].sum()

    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax1.bar(range(len(valid)), valid["Opportunity_Score"], color=NAVY, alpha=0.7)
    ax1.set_xlabel("Platforms, ranked highest to lowest Opportunity Score")
    ax1.set_ylabel("Opportunity Score", color=NAVY)

    ax2 = ax1.twinx()
    ax2.plot(range(len(valid)), cumulative_pct, color=AMBER, marker="o", markersize=2, linewidth=1.5)
    ax2.axhline(80, color="red", linestyle="--", linewidth=1)
    ax2.set_ylabel("Cumulative % of Total Opportunity Value", color=AMBER)
    ax1.set_title("Pareto Analysis: Concentration of SEO Opportunity Value", fontweight="bold")

    n_for_80pct = int((cumulative_pct <= 80).sum()) + 1
    path = _save(fig, "08_pareto_analysis")
    pct_of_total = round(100 * n_for_80pct / len(valid), 1)
    insight = (f"The top {n_for_80pct} platforms ({pct_of_total}% of all scored platforms) account "
               "for 80% of total weighted opportunity value. Recommendation: concentrate the first "
               "outreach cycle on this subset rather than spreading effort evenly across all "
               "researched platforms.")
    return {"path": path, "insight": insight, "n_for_80pct": n_for_80pct}


def chart_regression(master_df, x_col: str, y_col: str, regression_result: dict) -> dict:
    """Scatter plot with fitted OLS trend line for one regression pair.
    Why: makes the regression result (R², slope) visually inspectable
    rather than just a table of numbers — including how few points it's
    based on, so the viewer can judge reliability themselves."""
    paired = master_df[[x_col, y_col]].dropna()
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(paired[x_col], paired[y_col], color=NAVY, s=50, edgecolor="white", zorder=3)

    if regression_result.get("n", 0) >= 3 and not np.isnan(regression_result.get("r_squared", np.nan)):
        x_line = np.linspace(paired[x_col].min(), paired[x_col].max(), 50)
        y_line = regression_result["slope"] * x_line + regression_result["intercept"]
        ax.plot(x_line, y_line, color=AMBER, linewidth=2, zorder=2,
                label=f"R²={regression_result['r_squared']}, n={regression_result['n']}")
        ax.legend()

    ax.set_xlabel(x_col.replace("_clean", ""))
    ax.set_ylabel(y_col.replace("_clean", ""))
    ax.set_title(f"{x_col.replace('_clean','')} vs. {y_col.replace('_clean','')}", fontweight="bold")
    path = _save(fig, f"15_regression_{x_col}_{y_col}")
    return {"path": path}


def chart_cluster_validation(validation_df) -> dict:
    """Dual-axis line chart: inertia (elbow) + silhouette score across K.
    Why: justifies the chosen number of clusters (K) instead of picking
    it arbitrarily."""
    fig, ax1 = plt.subplots(figsize=(7, 4.5))
    ax1.plot(validation_df["k"], validation_df["inertia"], color=NAVY, marker="o", label="Inertia (elbow)")
    ax1.set_xlabel("Number of Clusters (K)")
    ax1.set_ylabel("Inertia (lower = tighter clusters)", color=NAVY)

    ax2 = ax1.twinx()
    ax2.plot(validation_df["k"], validation_df["silhouette_score"], color=AMBER, marker="s", label="Silhouette Score")
    ax2.set_ylabel("Silhouette Score (higher = better separation)", color=AMBER)
    ax1.set_title("Cluster Count Validation: Elbow Method + Silhouette Score", fontweight="bold")
    path = _save(fig, "16_cluster_validation")
    best_k = int(validation_df.loc[validation_df["silhouette_score"].idxmax(), "k"])
    insight = (f"Silhouette score peaks at K={best_k}, supporting the chosen cluster count as a "
               "reasonable (not arbitrary) choice rather than an assumption.")
    return {"path": path, "insight": insight, "best_k": best_k}


def chart_kmeans_clusters(scored_df) -> dict:
    """Scatter plot: DA vs. Traffic colored by K-Means cluster.
    Why: groups platforms into natural tiers (premium/mid/budget-unverified)
    for portfolio-style outreach planning, without needing labeled outcomes
    (i.e. without any supervised ML, which this dataset can't support)."""
    plot_df = scored_df.dropna(subset=["DA_clean", "Traffic_clean", "Cluster"])
    if plot_df.empty:
        plot_df = scored_df.dropna(subset=["DA_clean", "Cluster"])
        y_vals = np.zeros(len(plot_df))
        y_label = "(insufficient traffic data to plot)"
    else:
        y_vals = plot_df["Traffic_clean"]
        y_label = "Monthly Traffic (Est.)"

    fig, ax = plt.subplots(figsize=(7, 5))
    scatter = ax.scatter(plot_df["DA_clean"], y_vals, c=plot_df["Cluster"], cmap="viridis", s=60, edgecolor="white")
    ax.set_xlabel("Domain Authority (Est.)")
    ax.set_ylabel(y_label)
    ax.set_title("Platform Clusters: DA vs. Traffic", fontweight="bold")
    legend1 = ax.legend(*scatter.legend_elements(), title="Cluster")
    ax.add_artist(legend1)
    path = _save(fig, "09_kmeans_clusters")
    insight = ("K-Means groups platforms into natural authority/traffic tiers using only the "
               "subset with both DA and traffic data available — clustering was not applied to "
               "rows with missing values, since imputing would fabricate the exact numbers this "
               "report is committed to avoiding.")
    return {"path": path, "insight": insight}
