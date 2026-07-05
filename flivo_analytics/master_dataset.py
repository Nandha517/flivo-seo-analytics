"""
Flivo Backlink Opportunity Analytics — Master Dataset Builder
===============================================================
Section 2 of the pipeline: clean every sheet's numeric/text fields and
fold them into one unified, analysis-ready DataFrame (`master_df`) while
preserving sheet-of-origin, so cross-sheet business analysis is possible
without hardcoding six different schemas downstream.
"""
import numpy as np
import pandas as pd
from cleaning import (
    parse_traffic, parse_price, parse_numeric_metric,
    normalize_yes_no, is_custom_quote, is_qualitative_traffic
)

QUALITATIVE_MAP = {"high": 1.0, "medium-high": 0.75, "medium": 0.5,
                    "low-medium": 0.35, "low": 0.2, "unknown": np.nan}


def _food_relevance_score(value) -> float:
    """Map varied food-relevance style fields (Yes/Partial/No, or
    High/Medium/Low from Sheet 6) onto a common 0-1 scale."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    text = str(value).strip().lower()
    if text in QUALITATIVE_MAP:
        return QUALITATIVE_MAP[text]
    if text.startswith("yes"):
        return 1.0
    if text.startswith("partial"):
        return 0.5
    if text.startswith("no"):
        return 0.0
    return np.nan


def _guest_post_score(value) -> float:
    """Map Guest Post acceptance fields to 0/0.5/1."""
    norm = normalize_yes_no(value)
    return {"Yes": 1.0, "Limited": 0.5, "Partial": 0.5, "No": 0.0}.get(norm, np.nan)


def clean_free_platforms(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["DA_clean"] = out["DA (Est.)"].apply(parse_numeric_metric)
    out["DR_clean"] = out["DR (Est.)"].apply(parse_numeric_metric)
    traffic_col = "Monthly Organic Traffic (Est.)" if "Monthly Organic Traffic (Est.)" in out.columns else "Monthly Organic Traffic"
    out["Traffic_clean"] = out[traffic_col].apply(parse_traffic)
    out["Price_clean"] = 0.0  # Sheet 1 is exclusively free platforms
    out["Is_Custom_Quote"] = False
    out["Free_Paid"] = "Free"
    out["Guest_Post_Score"] = out["Guest Post Accepted"].apply(_guest_post_score)
    out["Food_Relevance_Score"] = out["Food/Health Content Accepted"].apply(_food_relevance_score)
    out["Name"] = out["Platform Name"]
    out["Category"] = out.get("Category", "Free Article Platform")
    return out


def clean_paid_platforms(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["DA_clean"] = out["DA (Est.)"].apply(parse_numeric_metric)
    out["DR_clean"] = out["DR (Est.)"].apply(parse_numeric_metric)
    out["Traffic_clean"] = out["Monthly Traffic (Est.)"].apply(parse_traffic)
    out["Price_clean"] = out["Price"].apply(parse_price)
    out["Is_Custom_Quote"] = out["Price"].apply(is_custom_quote)
    out["Free_Paid"] = "Paid"
    out["Guest_Post_Score"] = out["Guest Posts"].apply(_guest_post_score)
    out["Food_Relevance_Score"] = out["Food Content Accepted"].apply(_food_relevance_score)
    out["Name"] = out["Platform Name"]
    return out


def clean_food_niche(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["DA_clean"] = out["DA (Est.)"].apply(parse_numeric_metric)
    out["DR_clean"] = out["DR (Est.)"].apply(parse_numeric_metric)
    out["Traffic_clean"] = out["Traffic (Est.)"].apply(parse_traffic)
    out["Price_clean"] = out["Pricing"].apply(parse_price)
    out["Is_Custom_Quote"] = out["Pricing"].apply(is_custom_quote)
    out["Free_Paid"] = out["Pricing"].apply(
        lambda v: "Free" if isinstance(v, str) and v.strip().lower().startswith("free") else "Paid/Unclear")
    out["Guest_Post_Score"] = out["Guest Post"].apply(_guest_post_score)
    out["Food_Relevance_Score"] = out["Suitable for Flivo"].apply(_food_relevance_score)
    out["Name"] = out["Website"]
    out["Category"] = "Food & Health Niche Site"
    out["Benefits"] = out["Reason"]
    out["Limitations"] = ""
    return out


def clean_press_release(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["DA_clean"] = out["DA (Est.)"].apply(parse_numeric_metric)
    out["DR_clean"] = np.nan  # not collected for this sheet by design
    out["Traffic_clean"] = out["Traffic (Est.)"].apply(parse_traffic)
    out["Price_clean"] = out["Price"].apply(parse_price)
    out["Is_Custom_Quote"] = out["Price"].apply(is_custom_quote)
    out["Free_Paid"] = out["Price"].apply(
        lambda v: "Free" if isinstance(v, str) and "free" in v.lower() else "Paid")
    out["Guest_Post_Score"] = np.nan  # not applicable to PR wires
    out["Food_Relevance_Score"] = np.nan
    out["Name"] = out["Platform Name"]
    out["Category"] = "Press Release Platform"
    out["Limitations"] = ""
    return out


def clean_directories(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["DA_clean"] = out["DA (Est.)"].apply(parse_numeric_metric)
    out["DR_clean"] = np.nan
    out["Traffic_clean"] = out["Traffic (Est.)"].apply(parse_traffic)
    out["Price_clean"] = out["Free/Paid"].apply(
        lambda v: 0.0 if isinstance(v, str) and v.strip().lower().startswith("free") else np.nan)
    out["Is_Custom_Quote"] = False
    out["Free_Paid"] = out["Free/Paid"].apply(
        lambda v: "Free" if isinstance(v, str) and v.strip().lower().startswith("free") else "Paid")
    out["Guest_Post_Score"] = np.nan
    out["Food_Relevance_Score"] = out["Category"].apply(
        lambda v: 1.0 if isinstance(v, str) and "food" in v.lower() else np.nan)
    out["Name"] = out["Platform Name"]
    out["Benefits"] = out["Backlink Type"]
    out["Limitations"] = ""
    return out


def clean_top_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """Sheet 6 stores Authority/Traffic/Cost as qualitative labels
    (High/Medium/Low), not the same numeric DA/DR/Traffic scale used
    elsewhere. Mixing a rescaled qualitative label into DA_clean would
    silently corrupt cross-sheet DA statistics (e.g. every 'High' becoming
    a fake DA=100). These platforms already appear with real numeric data
    in their sheet of origin (Sheets 1-5), so Sheet 6 is deliberately kept
    numeric-NaN here and analyzed separately via its own qualitative
    Priority/Category breakdown (see business_analysis.top_recommendations_analysis)."""
    out = df.copy()
    out["DA_clean"] = np.nan
    out["DR_clean"] = np.nan
    out["Traffic_clean"] = np.nan
    out["Price_clean"] = np.nan
    out["Is_Custom_Quote"] = False
    out["Authority_Qualitative"] = out["Authority"]
    out["Traffic_Qualitative"] = out["Traffic"]
    out["Free_Paid"] = out["Category"].apply(
        lambda v: "Free" if isinstance(v, str) and "free" in v.lower() else "Paid/Mixed")
    out["Guest_Post_Score"] = np.nan
    out["Food_Relevance_Score"] = out["Food Relevance"].apply(_food_relevance_score)
    out["Name"] = out["Platform Name"]
    out["Benefits"] = out["Why Recommended"]
    out["Limitations"] = ""
    return out


CLEANERS = {
    "free_platforms": clean_free_platforms,
    "paid_platforms": clean_paid_platforms,
    "food_niche": clean_food_niche,
    "press_release": clean_press_release,
    "directories": clean_directories,
    "top_recommendations": clean_top_recommendations,
}

COMMON_COLUMNS = [
    "Name", "Sheet", "Category", "Free_Paid", "DA_clean", "DR_clean", "Traffic_clean",
    "Price_clean", "Is_Custom_Quote", "Guest_Post_Score", "Food_Relevance_Score",
    "Benefits", "Limitations",
]


# Sheet 6 (Top Recommendations) is a curated shortlist DRAWN FROM Sheets 1-5,
# not a distinct set of platforms. Including it in master_df would double-count
# every platform it references when computing KPIs like "Total Platforms" or
# "Free vs Paid split". It is analyzed separately via its own Priority/Category
# breakdown (see business_analysis.top_recommendations_analysis).
MASTER_DATASET_EXCLUDED_SHEETS = {"top_recommendations"}


def build_master_dataset(sheets: dict) -> pd.DataFrame:
    """Clean every sheet with its dedicated cleaner and stack into one
    unified DataFrame with a consistent schema for cross-sheet analysis."""
    frames = []
    for key, df in sheets.items():
        if key in MASTER_DATASET_EXCLUDED_SHEETS:
            continue
        cleaner = CLEANERS.get(key)
        if cleaner is None:
            continue
        try:
            cleaned = cleaner(df)
        except KeyError as exc:
            raise KeyError(f"Expected column missing while cleaning sheet '{key}': {exc}") from exc
        cleaned["Sheet"] = key
        for col in COMMON_COLUMNS:
            if col not in cleaned.columns:
                cleaned[col] = np.nan
        frames.append(cleaned[COMMON_COLUMNS])
    master = pd.concat(frames, ignore_index=True)
    master = master.drop_duplicates(subset=["Name", "Sheet"]).reset_index(drop=True)
    return master


if __name__ == "__main__":
    from ingest import load_all_sheets
    sheets = load_all_sheets()
    master = build_master_dataset(sheets)
    print(master.shape)
    print(master.head(10).to_string())
    print("\nNulls per column:\n", master.isna().sum())
