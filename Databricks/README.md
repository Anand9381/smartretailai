Databricks — Summary

This folder contains a short summary of the Databricks work used in the Smart Retail Capstone.

Key points (simple):
- Workspace: a Databricks workspace was used to run PySpark notebooks for data transformation and lightweight feature engineering.
- Notebook: `retail_pipeline` (example) reads the staged CSV from Azure Blob Storage, applies transformations (type casting, stock status, simple aggregations) and displays a small products table.
- Compute: Serverless or interactive cluster was used for development; notebook run completed successfully and returned sample rows (8 rows shown in screenshots).
- ML: Databricks notebook demonstrates simple forecasting steps (data load → day-index feature → training a regression model) — equivalent to the `ml_model.py` in the repo. Forecast outputs were validated and sample predictions produced.
- Output: cleaned/curated data can be written back to `smart-retail-data/curated` or pushed to the database (Cosmos/Mongo) depending on pipeline configuration.

How it fits:
- Databricks performs the transform and ML workload in the Raw→Staged→Curated workflow triggered / orchestrated by ADF.
- Use the notebook to reproduce transformations and to experiment with model features before embedding the final model into the `ml_model.py` module.
