"""
Flivo Backlink Opportunity Analytics — Business Analysis
==========================================================
Sections 3-9 of the pipeline. Every function returns a small, clean
DataFrame or dict ready for reporting/export — no raw statistical dumps.
"""
import numpy as np
import pandas as pd


def seo_kpi_summary(master_df: pd.DataFrame, sheets: dict) -> pd.DataFrame:
    """Section 3: Overall Dataset Summary + SEO KPI Summary."""
    kpis = {
        "Total Platforms (all sheets)": len(master_df),
        "Free Platforms": int((master_df["Free_Paid"] == "Free").sum()),
        "Paid Platforms": int(master_df["Free_Paid"].isin(["Paid", "Paid/Unclear", "Paid/Mixed"]).sum()),
        "Food & Health Niche Sites": len(sheets["food_niche"]),
        "Press Release Platforms": len(sheets["press_release"]),
        "Business Directories": len(sheets["directories"]),
        "Platforms Accepting Guest Posts (score>=0.5)": int((master_df["Guest_Post_Score"] >= 0.5).sum()),
        "Platforms with Verified/Estimated DA": int(master_df["DA_clean"].notna().sum()),
        "Platforms with DA = N/A (unverified)": int(master_df["DA_clean"].isna().sum()),
    }
    return pd.DataFrame(list(kpis.items()), columns=["KPI", "Value"])


def domain_authority_analysis(master_df: pd.DataFrame) -> dict:
    """Section 4: DA distribution stats, restricted to non-null values.
    Sample size (n) is always reported alongside stats since a large share
    of rows are legitimately unverified (see data-sourcing note)."""
    valid = master_df["DA_clean"].dropna()
    return {
        "n_with_data": int(valid.count()),
        "n_missing": int(master_df["DA_clean"].isna().sum()),
        "mean": round(valid.mean(), 1) if not valid.empty else np.nan,
        "median": round(valid.median(), 1) if not valid.empty else np.nan,
        "min": valid.min() if not valid.empty else np.nan,
        "max": valid.max() if not valid.empty else np.nan,
        "top_5": master_df.nlargest(5, "DA_clean")[["Name", "Sheet", "DA_clean"]].to_dict("records"),
    }


def domain_rating_analysis(master_df: pd.DataFrame) -> dict:
    """Section 5: DR distribution stats."""
    valid = master_df["DR_clean"].dropna()
    return {
        "n_with_data": int(valid.count()),
        "n_missing": int(master_df["DR_clean"].isna().sum()),
        "mean": round(valid.mean(), 1) if not valid.empty else np.nan,
        "median": round(valid.median(), 1) if not valid.empty else np.nan,
        "top_5": master_df.nlargest(5, "DR_clean")[["Name", "Sheet", "DR_clean"]].to_dict("records"),
    }


def traffic_analysis(master_df: pd.DataFrame) -> dict:
    """Section 6: Traffic distribution stats (numeric-only; qualitative-only
    descriptors like 'Very High' are excluded from the mean but not lost —
    they remain visible in the source workbook)."""
    valid = master_df["Traffic_clean"].dropna()
    return {
        "n_with_numeric_data": int(valid.count()),
        "n_missing_or_qualitative_only": int(master_df["Traffic_clean"].isna().sum()),
        "mean": round(valid.mean(), 0) if not valid.empty else np.nan,
        "median": round(valid.median(), 0) if not valid.empty else np.nan,
        "top_5": master_df.nlargest(5, "Traffic_clean")[["Name", "Sheet", "Traffic_clean"]].to_dict("records"),
    }


def pricing_analysis(master_df: pd.DataFrame) -> pd.DataFrame:
    """Section 7: Cost distribution by category, restricted to paid platforms
    with a real published price (Contact Sales/Custom Quote excluded from
    the numeric stats but counted separately)."""
    paid = master_df[master_df["Free_Paid"].isin(["Paid", "Paid/Unclear"])]
    priced = paid[paid["Price_clean"].notna() & (~paid["Is_Custom_Quote"])]

    summary = priced.groupby("Category")["Price_clean"].agg(
        count="count", mean="mean", median="median", min="min", max="max"
    ).round(1).sort_values("mean", ascending=False)

    custom_quote_count = int(paid["Is_Custom_Quote"].sum())
    summary.attrs["custom_quote_count"] = custom_quote_count
    return summary


def guest_posting_analysis(master_df: pd.DataFrame) -> pd.DataFrame:
    """Section 8: Guest-post acceptance rate by sheet."""
    def rate(series):
        valid = series.dropna()
        return round(100 * (valid >= 0.5).mean(), 1) if not valid.empty else np.nan

    return master_df.groupby("Sheet")["Guest_Post_Score"].agg(
        n_platforms="count",
        guest_post_acceptance_pct=rate,
    )


def food_website_analysis(sheets: dict) -> pd.DataFrame:
    """Section 9: Food & Health niche suitability breakdown."""
    food_df = sheets["food_niche"]
    counts = food_df["Suitable for Flivo"].value_counts()
    pct = (counts / counts.sum() * 100).round(1)
    return pd.DataFrame({"Count": counts, "Percent": pct})


def business_directory_analysis(sheets: dict) -> pd.DataFrame:
    """Section 9b: Business directory free/paid and backlink-type split."""
    dir_df = sheets["directories"]
    free_paid_counts = dir_df["Free/Paid"].apply(
        lambda v: "Free" if isinstance(v, str) and v.strip().lower().startswith("free") else "Paid"
    ).value_counts()
    return free_paid_counts.to_frame("Count")


def top_recommendations_analysis(sheets: dict) -> pd.DataFrame:
    """Section 10: Priority breakdown from the Top Recommendations sheet."""
    top_df = sheets["top_recommendations"]
    return top_df.groupby(["Priority", "Category"]).size().unstack(fill_value=0)
