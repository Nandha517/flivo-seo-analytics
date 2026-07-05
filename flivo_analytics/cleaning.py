"""
Flivo Backlink Opportunity Analytics — Cleaning Utilities
==========================================================
Reusable, well-tested parsing functions. Every function fails soft
(returns NaN) rather than raising, since messy real-world SEO data
is the norm, not the exception.
"""
import re
import numpy as np
import pandas as pd
from config import MISSING_TOKENS


def is_missing_token(value) -> bool:
    """Return True if a string value represents an intentional non-value
    (N/A, Contact Sales, Custom Quote, etc.) rather than real data."""
    if value is None:
        return True
    if isinstance(value, float) and np.isnan(value):
        return True
    text = str(value).strip().lower()
    if text in MISSING_TOKENS:
        return True
    # Catch compound strings like "N/A - varies per site (...)" or
    # "Contact Sales" embedded mid-sentence at the start of the field.
    if text.startswith("n/a") or text.startswith("contact sales") or text.startswith("custom quote"):
        return True
    return False


def parse_traffic(value):
    """
    Convert traffic strings like '250K', '3.2M', '1.8B', '100M+ monthly',
    'Very High', 'Massive' into a numeric estimate (float) or NaN.

    Qualitative-only descriptors (no number present) are mapped to NaN
    rather than guessed at, and are tracked separately via
    `traffic_is_qualitative` so they are never silently treated as zero.
    """
    if is_missing_token(value):
        return np.nan
    text = str(value).strip()

    match = re.search(r"([\d.]+)\s*([KMB])", text, re.IGNORECASE)
    if match:
        number = float(match.group(1))
        suffix = match.group(2).upper()
        multiplier = {"K": 1e3, "M": 1e6, "B": 1e9}[suffix]
        return number * multiplier

    # Plain numeric traffic (rare, but handle it)
    match_plain = re.search(r"^\s*([\d,]+)\s*$", text)
    if match_plain:
        return float(match_plain.group(1).replace(",", ""))

    return np.nan  # qualitative-only ("Very High", "Massive", "Moderate", etc.)


def is_qualitative_traffic(value) -> bool:
    """True if the field has a real qualitative traffic descriptor
    (e.g. 'Very High') that parse_traffic() could not convert to a number,
    as opposed to being genuinely missing."""
    if is_missing_token(value):
        return False
    return pd.isna(parse_traffic(value)) and isinstance(value, str) and value.strip() != ""


def parse_price(value):
    """
    Convert price fields to a single representative numeric value (float).

    Handles:
      - Plain numbers: 129 -> 129.0
      - Ranges: '15-1000+' -> midpoint of 15 and 1000 (2000/2 truncating '+')
      - 'From 29' -> 29.0
      - 'Contact Sales' / 'Custom Quote' -> NaN (flagged separately)
    """
    if is_missing_token(value):
        return np.nan
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().lower().replace("$", "").replace(",", "")
    text = text.replace("from ", "")

    # Range like "15-1000+" or "99-389"
    range_match = re.match(r"^([\d.]+)\s*-\s*([\d.]+)\+?", text)
    if range_match:
        low, high = float(range_match.group(1)), float(range_match.group(2))
        return round((low + high) / 2, 2)

    # Single number possibly with trailing '+'
    single_match = re.match(r"^([\d.]+)\+?", text)
    if single_match:
        return float(single_match.group(1))

    return np.nan


def is_custom_quote(value) -> bool:
    """True if pricing requires direct sales contact (no public number)."""
    if value is None:
        return False
    text = str(value).strip().lower()
    return text.startswith("contact sales") or text.startswith("custom quote")


def parse_numeric_metric(value):
    """Generic numeric parser for DA/DR style columns: '65', 'N/A', '55' -> float or NaN."""
    if is_missing_token(value):
        return np.nan
    text = str(value).strip()
    match = re.search(r"[\d.]+", text)
    return float(match.group(0)) if match else np.nan


def normalize_yes_no(value):
    """Standardize Yes/No/Limited/Partial style fields into a clean category."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "Unknown"
    text = str(value).strip().lower()
    if text.startswith("yes"):
        return "Yes"
    if text.startswith("no"):
        return "No"
    if text.startswith("limited"):
        return "Limited"
    if text.startswith("partial"):
        return "Partial"
    return "Unknown"


def min_max_normalize(series: pd.Series) -> pd.Series:
    """Normalize a numeric series to 0-1. NaNs pass through as NaN (never zero-filled),
    so missing data is excluded from scoring rather than penalized as 'worst'."""
    valid = series.dropna()
    if valid.empty or valid.max() == valid.min():
        return series.apply(lambda x: np.nan if pd.isna(x) else 0.5)
    return (series - valid.min()) / (valid.max() - valid.min())
