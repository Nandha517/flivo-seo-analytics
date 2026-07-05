"""
Flivo Backlink Opportunity Analytics — Configuration
=====================================================
Central place for constants, weights, and paths so nothing is hardcoded
inline across the pipeline.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE_WORKBOOK = os.path.join(BASE_DIR, "Flivo_Backlink_Research.xlsx")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
CHARTS_DIR = os.path.join(BASE_DIR, "outputs", "charts")

# Sheet name -> short internal key (dynamic lookup still validates these exist)
SHEET_MAP = {
    "1. Free Article Platforms": "free_platforms",
    "2. Paid Article Platforms": "paid_platforms",
    "3. Food & Health Niche Sites": "food_niche",
    "4. Press Release Platforms": "press_release",
    "5. Business Directories": "directories",
    "6. Top Recommendations": "top_recommendations",
}

# Strings that represent "intentionally unknown" rather than a parsing failure.
MISSING_TOKENS = {
    "n/a", "na", "unknown", "contact sales", "custom quote", "-", "", "none",
    "verify current status", "reported yes - verify current status",
}

# Opportunity Score weights (must sum to 1.0) — per assignment brief
OPPORTUNITY_WEIGHTS = {
    "DA": 0.30,
    "DR": 0.20,
    "Traffic": 0.20,
    "Food_Relevance": 0.15,
    "Guest_Post": 0.10,
    "Cost_Efficiency": 0.05,
}

assert abs(sum(OPPORTUNITY_WEIGHTS.values()) - 1.0) < 1e-9, "Opportunity weights must sum to 1.0"

RANDOM_STATE = 42
N_CLUSTERS = 3  # Premium / Mid-tier / Budget-or-Unverified
