Databricks - Summary

This folder contains a short summary of the Databricks work used in the Smart Retail Capstone.

Key points:
- Workspace: a Databricks workspace was used to run PySpark notebooks for data transformation and lightweight feature engineering.
- Notebook: `retail_pipeline` reads the staged CSV from Azure Blob Storage, applies transformations such as type casting, stock status, and simple aggregations, then displays a small products table.
- Compute: Serverless or an interactive cluster was used for development; the notebook run completed successfully and returned sample rows.
- ML: The notebook demonstrates simple forecasting steps: data load, day-index feature creation, and regression model training. This matches the local `ml_model.py` flow in the repo.
- Output: Cleaned or curated data can be written back to `smart-retail-data/curated` or pushed to MongoDB Atlas.

How it fits:
- Databricks performs the transform and ML workload in the Raw -> Staged -> Curated workflow triggered or orchestrated by ADF.
- Use the notebook to reproduce transformations and experiment with model features before embedding the final model into `ml_model.py`.
