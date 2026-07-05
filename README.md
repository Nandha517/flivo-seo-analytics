## Flivo SEO Backlink Opportunity Analytics ##

Python analytics pipeline for Flivo's SEO backlink opportunity research — data cleaning, KPI analysis, clustering, regression, weighted opportunity scoring, and visualizations. 

## Project Overview ##

Flivo is a D2C healthy food and nutrition brand. This project takes a manually researched backlink opportunity dataset — covering free article publishing platforms, paid guest-post and sponsored-content platforms, food and health niche websites, press release distribution platforms, and business directories — and runs it through a full Python analytics pipeline to produce a prioritized, statistically grounded set of SEO outreach recommendations.

The original dataset was compiled through manual research of each platform's official write-for-us pages, guest-post guidelines, advertising and media-kit pages, and contact pages, cross-referenced against recent SEO industry publications for pricing and authority context. Wherever a Domain Authority, Domain Rating, or traffic figure could not be verified from a credible source, it was recorded as N/A rather than estimated, and wherever pricing was not publicly published, it was recorded as Contact Sales or Custom Quote. This means every number in the dataset is either a real, attributable figure or an honest gap, never a guess.

## What the Pipeline Does ##

The pipeline loads all six research sheets dynamically, audits each one for missing values and duplicates, and cleans every sheet's DA, DR, traffic, and pricing fields into standardized numeric values, converting messy real-world formats like traffic strings ("250K", "3.2M", "100M+ monthly") and price ranges ("15-1000+") into usable numbers. All cleaned sheets are then combined into one unified master dataset for cross-sheet analysis.

On top of that cleaned dataset, the pipeline computes an SEO KPI summary covering total platforms, free versus paid splits, guest-post acceptance rates, and data completeness; runs Domain Authority, Domain Rating, traffic, and pricing distribution analysis restricted to verified data only; analyzes guest-posting acceptance and food/health niche suitability; builds a correlation matrix across the numeric fields; runs K-Means clustering to group platforms into authority tiers, validated with the elbow method and silhouette score rather than picking a cluster count arbitrarily; runs simple linear regression to quantify observed relationships between Domain Authority, Domain Rating, and traffic, used descriptively rather than predictively since the dataset has no historical outcome labels to train a predictive model on; computes a weighted Opportunity Score combining Domain Authority, Domain Rating, traffic, food relevance, guest-post availability, and cost efficiency, with an explicit eligibility rule so platforms with too little real data are excluded from ranking rather than scored on guesswork; runs a Pareto analysis to identify which platforms account for 80% of total opportunity value; identifies Quick Wins and Long-Term Opportunities; and models a sample monthly budget allocation. Word clouds and keyword-frequency charts are generated from the Benefits, Limitations, and recommendation text fields, and every chart is produced with Matplotlib alongside a written explanation of why it was created and what it implies for Flivo.

No supervised machine learning methods (logistic regression, random forest, neural networks, decision trees, Naive Bayes, time series, or PCA) are used in this project. This is a deliberate methodological decision rather than a limitation: the dataset has no historical record of which backlinks succeeded or failed, so a supervised model would have nothing valid to learn from and would simply overfit noise on a roughly hundred-row dataset. PCA was excluded because there are only a handful of partially populated numeric fields, too few and too sparse for dimensionality reduction to be meaningful. Unsupervised and transparent methods — clustering, weighted scoring, correlation, and descriptive regression — were used instead because every result can be traced back to its exact inputs, which matters when the output needs to be defended to a non-technical founder audience.

## Tools and Technologies ##

Python 3.12, pandas, NumPy, openpyxl, Matplotlib, scikit-learn, SciPy, and WordCloud. The project is organized as a modular package rather than a single script, with separate modules for configuration, data cleaning, ingestion, the master dataset builder, business analysis, advanced analytics, regression, visualizations, text analytics, exports, and the main orchestration script, so each stage can be tested, re-run, and audited independently.

 ## Setup ##

Create a virtual environment, activate it, and install the dependencies listed in requirements.txt. Then run main.py from inside the flivo_analytics folder. The script will print progress for each section as it runs, and on completion will create an outputs folder containing the final analytics Excel report, the original research workbook with an appended Analysis Summary tab, and a charts folder with every visualization generated during the run.

## Key Finding ##

Only around one in five platforms in the dataset currently have enough verified Domain Authority, Domain Rating, and traffic data to be scored and ranked with confidence. This is treated as the most important and most actionable finding in the project: rather than filling that gap with invented numbers, the pipeline flags it explicitly and the accompanying methodology report identifies manual DA/DR verification of the remaining platforms as the single highest-leverage next step before scaling any paid SEO spend.

## Outputs ##

Running the pipeline produces a cleaned and standardized dataset, a weighted opportunity ranking across all analyzed platforms, a Quick Wins and Long-Term Opportunities breakdown, a sample budget allocation plan, statistical summary tables for Domain Authority, Domain Rating, traffic, and pricing, a full set of charts and word clouds, and a final consolidated Excel report. A separate methodology and findings report documents how the original dataset was compiled, what each pipeline step does and why, what the statistics actually show, and the resulting strategic recommendations for short-term and long-term SEO strategy.