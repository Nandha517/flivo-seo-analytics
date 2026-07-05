# Flivo Backlink Opportunity Analytics — VS Code Setup

## Folder structure (already set up in this zip)
```
flivo-seo-analytics/
├── flivo_analytics/          <- all the Python modules
│   ├── config.py
│   ├── cleaning.py
│   ├── ingest.py
│   ├── master_dataset.py
│   ├── business_analysis.py
│   ├── advanced_analytics.py
│   ├── visuals.py
│   ├── text_analytics.py
│   ├── exports.py
│   └── main.py
├── Flivo_Backlink_Research.xlsx   <- the source data (already included)
└── requirements.txt
```

## Steps

1. **Unzip this folder** anywhere on your computer.
2. **Open it in VS Code**: `File → Open Folder...` → select `flivo-seo-analytics`.
3. **Open a terminal in VS Code**: `Terminal → New Terminal` (or `` Ctrl+` ``).
4. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   ```
   On Windows use `python` instead of `python3` if needed.
5. **Activate it**:
   - macOS/Linux: `source venv/bin/activate`
   - Windows (PowerShell): `venv\Scripts\Activate.ps1`
   - Windows (cmd): `venv\Scripts\activate.bat`

   You should see `(venv)` appear at the start of your terminal prompt.
6. **Select the interpreter in VS Code**: press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac), type "Python: Select Interpreter", choose the one inside `venv`.
7. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
8. **Run the pipeline**:
   ```bash
   cd flivo_analytics
   python main.py
   ```

## What's new in this version
- **Regression analysis** (`regression.py`): tests whether DA predicts Traffic, whether DA and DR agree, etc. — used only as *descriptive* regression (quantifying an observed relationship), never as predictive ML, since the dataset has no historical outcome labels to predict.
- **Cluster validation** (`validate_cluster_count` in `advanced_analytics.py`): elbow method + silhouette score across K=2-5, so the 3-cluster choice is justified rather than arbitrary.
- **`Flivo_Analytics_Methodology_Report.docx`**: the full write-up — how the dataset was compiled, what every pipeline step does and why, what the statistics say, and the strategic recommendations. Ready to submit as-is or adapt.

## What happens when you run it

You'll see section-by-section progress in the terminal (ingestion → cleaning → KPIs → advanced analytics → charts → exports). When it finishes, a new `outputs/` folder appears at the project root containing:

- `Flivo_Backlink_Analysis_Report.xlsx` — full analytics workbook with charts
- `Flivo_Backlink_Opportunity_Research.xlsx` — your original workbook + an appended "Analysis Summary" tab
- `charts/` — all PNG charts and word clouds

## Recommended VS Code extensions
- **Python** (Microsoft) — required for running/debugging `.py` files
- **Excel Viewer** — preview `.xlsx` output files without leaving VS Code

## If something fails
The pipeline is designed to fail loudly with a full traceback rather than silently producing wrong output — if you see `FAILED in section '...'`, that error message tells you exactly which step and why (usually a missing package or a changed file path).
