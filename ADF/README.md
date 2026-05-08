Azure Data Factory (ADF) — Summary

This folder contains a short summary of the Azure Data Factory work used in the Smart Retail Capstone.

Key points (simple):
- Purpose: ingest raw CSV files from Azure Blob Storage into the data engineering workspace and copy to staged/curated folders.
- Pipeline: `pipeline1` created with a Copy Data activity. Datasets: `DelimitedText1`, `DelimitedText2`.
- Storage: blobs are organized into containers/paths: `smart-retail-data/raw`, `smart-retail-data/staged`, `smart-retail-data/curated` (see screenshots provided in project).
- Execution: pipeline debug/run shows "Succeeded"; copy activity moves `retail_master_dataset.csv` into the `raw` folder and downstream steps perform simple staging.
- How it fits: ADF is used for orchestration (ingest and land raw files). Downstream compute (Databricks / PySpark) reads staged data for cleaning and ML.

Notes for evaluators:
- The ADF pipeline is minimal and demonstrates the Raw→Staged→Curated flow required by the project.
- You can re-run the pipeline in the Azure portal under Data Factory → Pipelines → `pipeline1`.
