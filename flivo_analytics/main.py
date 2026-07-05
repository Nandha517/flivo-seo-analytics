"""
Flivo Backlink Opportunity Analytics — Main Pipeline
=======================================================
Runs every section in order, printing progress checkpoints. Designed to
fail loudly (via exceptions) rather than silently producing wrong output.
"""
import sys
import traceback
import pandas as pd

from ingest import load_all_sheets, audit_all_sheets
from master_dataset import build_master_dataset
from business_analysis import (
    seo_kpi_summary, domain_authority_analysis, domain_rating_analysis,
    traffic_analysis, pricing_analysis, guest_posting_analysis,
    food_website_analysis, business_directory_analysis, top_recommendations_analysis
)
from advanced_analytics import (
    correlation_matrix, run_kmeans, compute_opportunity_score,
    pareto_table, quick_wins_and_long_term, budget_optimization,
    validate_cluster_count
)
from regression import run_all_regressions, interpret_regression
from visuals import (
    chart_free_vs_paid, chart_platforms_per_sheet, chart_da_distribution,
    chart_pricing_by_category, chart_guest_post_acceptance, chart_food_suitability,
    chart_opportunity_score_top20, chart_pareto, chart_kmeans_clusters,
    chart_regression, chart_cluster_validation
)
from text_analytics import generate_wordcloud, chart_keyword_frequency
from exports import export_analysis_workbook, append_analysis_summary_to_original


def checkpoint(msg):
    print(f"\n{'='*70}\n{msg}\n{'='*70}")


def run_section(name, func, *args, **kwargs):
    checkpoint(f"SECTION: {name}")
    try:
        result = func(*args, **kwargs)
        print(f"  OK")
        return result
    except Exception:
        print(f"  FAILED in section '{name}':")
        traceback.print_exc()
        sys.exit(1)


def main():
    # ---------------- Section 1: Ingestion & Audit ----------------
    sheets = run_section("1. Load workbook", load_all_sheets)
    audit_df = run_section("1b. Audit sheets", audit_all_sheets, sheets)
    print(audit_df.to_string(index=False))

    # ---------------- Section 2: Cleaning ----------------
    master_df = run_section("2. Build cleaned master dataset", build_master_dataset, sheets)
    print(f"  Master dataset shape: {master_df.shape}")

    # ---------------- Section 3-9: Business Analysis ----------------
    kpi_df = run_section("3. SEO KPI Summary", seo_kpi_summary, master_df, sheets)
    print(kpi_df.to_string(index=False))

    da_stats = run_section("4. Domain Authority Analysis", domain_authority_analysis, master_df)
    dr_stats = run_section("5. Domain Rating Analysis", domain_rating_analysis, master_df)
    traffic_stats = run_section("6. Traffic Analysis", traffic_analysis, master_df)
    pricing_df = run_section("7. Pricing Analysis", pricing_analysis, master_df)
    guest_post_df = run_section("8. Guest Posting Analysis", guest_posting_analysis, master_df)
    food_df = run_section("9. Food Website Analysis", food_website_analysis, sheets)
    dir_df = run_section("9b. Business Directory Analysis", business_directory_analysis, sheets)
    top_rec_df = run_section("10. Top Recommendations Analysis", top_recommendations_analysis, sheets)

    # ---------------- Advanced Analytics ----------------
    corr_df = run_section("11. Correlation Matrix", correlation_matrix, master_df)
    clustered_df = run_section("12. K-Means Clustering", run_kmeans, master_df)
    scored_df = run_section("13. Opportunity Score", compute_opportunity_score, clustered_df)
    pareto_df = run_section("14. Pareto Analysis", pareto_table, scored_df)
    quick_wins_df, long_term_df = run_section("15. Quick Wins / Long-Term", quick_wins_and_long_term, scored_df)
    budget_df = run_section("16. Budget Optimization", budget_optimization, scored_df, 500)

    # ---------------- Regression & Cluster Validation ----------------
    regression_df = run_section("16b. Regression Analysis", run_all_regressions, master_df)
    print(regression_df.to_string(index=False))
    for _, row in regression_df.iterrows():
        print("  ->", interpret_regression(row.to_dict()))
    cluster_validation_df = run_section("16c. Cluster Count Validation", validate_cluster_count, master_df)
    print(cluster_validation_df.to_string(index=False))

    # ---------------- Visualizations ----------------
    checkpoint("SECTION: 17. Visualizations")
    chart_results = []
    chart_results.append(run_section("  Free vs Paid", chart_free_vs_paid, master_df))
    chart_results.append(run_section("  Platforms per sheet", chart_platforms_per_sheet, master_df))
    chart_results.append(run_section("  DA distribution", chart_da_distribution, master_df))
    chart_results.append(run_section("  Pricing by category", chart_pricing_by_category, pricing_df))
    chart_results.append(run_section("  Guest post acceptance", chart_guest_post_acceptance, guest_post_df))
    chart_results.append(run_section("  Food suitability", chart_food_suitability, food_df))
    chart_results.append(run_section("  Opportunity score top 20", chart_opportunity_score_top20, scored_df))
    chart_results.append(run_section("  Pareto", chart_pareto, scored_df))
    chart_results.append(run_section("  K-Means clusters", chart_kmeans_clusters, scored_df))
    chart_results.append(run_section("  Regression: DA vs Traffic", chart_regression, master_df,
                                      "DA_clean", "Traffic_clean", regression_df.iloc[0].to_dict()))
    chart_results.append(run_section("  Regression: DA vs DR", chart_regression, master_df,
                                      "DA_clean", "DR_clean", regression_df.iloc[1].to_dict()))
    chart_results.append(run_section("  Cluster validation (elbow/silhouette)", chart_cluster_validation,
                                      cluster_validation_df))
    chart_paths = [c["path"] for c in chart_results if c.get("path")]

    # ---------------- Text Analytics ----------------
    checkpoint("SECTION: 18. Text Analytics")
    benefits_wc = run_section("  Benefits word cloud", generate_wordcloud,
                               master_df["Benefits"].tolist(), "Benefits — Word Cloud", "10_wc_benefits", "Greens")
    limitations_wc = run_section("  Limitations word cloud", generate_wordcloud,
                                  master_df["Limitations"].tolist(), "Limitations — Word Cloud", "11_wc_limitations", "Oranges")
    recommend_wc = run_section("  Recommendation word cloud", generate_wordcloud,
                                sheets["top_recommendations"]["Why Recommended"].tolist(),
                                "Top Recommendations — Why — Word Cloud", "12_wc_recommendations", "Blues")
    food_wc = run_section("  Food niche word cloud", generate_wordcloud,
                           sheets["food_niche"]["Reason"].tolist(), "Food Niche Fit — Word Cloud", "13_wc_food_niche", "viridis")

    kw_chart_path = run_section("  Top keywords bar chart", chart_keyword_frequency,
                                 benefits_wc["top_keywords"], "Top Keywords in 'Benefits' Field", "14_top_keywords_benefits")
    if kw_chart_path:
        chart_paths.append(kw_chart_path)
    for wc in (benefits_wc, limitations_wc, recommend_wc, food_wc):
        if wc.get("path"):
            chart_paths.append(wc["path"])

    # ---------------- Exports ----------------
    checkpoint("SECTION: 19. Exports")
    report_path = run_section(
        "  Export standalone analysis workbook", export_analysis_workbook,
        scored_df, scored_df, pareto_df, kpi_df, da_stats, dr_stats, traffic_stats,
        pricing_df, guest_post_df, food_df, quick_wins_df, long_term_df, budget_df,
        corr_df, chart_paths
    )
    print(f"  Saved: {report_path}")

    summary_path = run_section(
        "  Append Analysis Summary tab to original workbook",
        append_analysis_summary_to_original, kpi_df, pareto_df
    )
    print(f"  Saved: {summary_path}")

    # ---------------- Final Report Data (for narrative write-up) ----------------
    checkpoint("PIPELINE COMPLETE")
    print(f"Total platforms analyzed: {len(master_df)}")
    print(f"Platforms eligible for a full Opportunity Score: {scored_df['Score_Eligible'].sum()}")
    print(f"Top 10 opportunities:")
    print(pareto_df.head(10)[["Rank", "Name", "Sheet", "Opportunity_Score"]].to_string(index=False))
    print(f"\nQuick Wins identified: {len(quick_wins_df)}")
    print(f"Long-Term Opportunities identified: {len(long_term_df)}")

    return {
        "master_df": master_df, "scored_df": scored_df, "pareto_df": pareto_df,
        "kpi_df": kpi_df, "quick_wins_df": quick_wins_df, "long_term_df": long_term_df,
        "budget_df": budget_df, "chart_paths": chart_paths,
    }


if __name__ == "__main__":
    main()
