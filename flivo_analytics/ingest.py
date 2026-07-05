"""
Flivo Backlink Opportunity Analytics — Ingestion & Audit
=========================================================
Section 1 of the pipeline: load every data sheet dynamically, and produce
a data-quality audit (shape, dtypes, missing values, duplicates,
completeness) before any cleaning happens.
"""
import pandas as pd
from config import SOURCE_WORKBOOK, SHEET_MAP
from cleaning import is_missing_token


def load_all_sheets(path: str = SOURCE_WORKBOOK) -> dict:
    """Dynamically load every sheet in the workbook except the narrative
    Executive Summary tab (which has no tabular structure)."""
    try:
        xl = pd.ExcelFile(path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Workbook not found at {path}") from exc

    sheets = {}
    for sheet_name in xl.sheet_names:
        if sheet_name.strip().lower() == "executive summary":
            continue
        df = xl.parse(sheet_name)
        key = SHEET_MAP.get(sheet_name, sheet_name)  # fall back to raw name if unmapped
        sheets[key] = df
    return sheets


def audit_sheet(name: str, df: pd.DataFrame) -> dict:
    """Produce a data-quality summary for a single sheet."""
    n_rows, n_cols = df.shape

    missing_counts = {}
    for col in df.columns:
        missing = df[col].apply(is_missing_token).sum()
        missing_counts[col] = missing

    total_cells = n_rows * n_cols
    total_missing = sum(missing_counts.values())
    completeness_pct = round(100 * (1 - total_missing / total_cells), 1) if total_cells else 0.0

    duplicate_rows = int(df.duplicated().sum())
    # Duplicate platform/website names specifically (first column is usually the name/website)
    name_col_candidates = [c for c in df.columns if c.lower() in
                            ("platform name", "website", "s.no")]
    name_col = next((c for c in df.columns if "name" in c.lower() or c.lower() == "website"), None)
    duplicate_names = int(df[name_col].duplicated().sum()) if name_col else None

    return {
        "sheet": name,
        "rows": n_rows,
        "columns": n_cols,
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_per_column": missing_counts,
        "total_missing_cells": int(total_missing),
        "completeness_pct": completeness_pct,
        "duplicate_rows": duplicate_rows,
        "duplicate_names": duplicate_names,
    }


def audit_all_sheets(sheets: dict) -> pd.DataFrame:
    """Run audit_sheet across every loaded sheet and return a tidy summary table."""
    records = []
    for name, df in sheets.items():
        result = audit_sheet(name, df)
        records.append({
            "Sheet": result["sheet"],
            "Rows": result["rows"],
            "Columns": result["columns"],
            "Completeness %": result["completeness_pct"],
            "Missing Cells": result["total_missing_cells"],
            "Duplicate Rows": result["duplicate_rows"],
            "Duplicate Names": result["duplicate_names"],
        })
    return pd.DataFrame(records)


if __name__ == "__main__":
    sheets = load_all_sheets()
    print(f"Loaded {len(sheets)} sheets: {list(sheets.keys())}\n")
    audit_df = audit_all_sheets(sheets)
    print(audit_df.to_string(index=False))
