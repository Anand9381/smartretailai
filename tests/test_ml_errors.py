"""
test_ml_errors.py - Tests for ML error handling
================================================

These tests check that the ML module logs and raises appropriate
exceptions when critical resources (CSV data or training data) are
missing or invalid. They are simple and explainable for learning.
"""

import pytest
import pandas as pd

import ml_model


def test_load_sales_missing_csv_raises(monkeypatch):
    """When MongoDB is not available and CSV is missing, FileNotFoundError should bubble up."""
    # Ensure we do not attempt to use a real MongoDB in the test
    monkeypatch.setattr(ml_model, "MongoClient", None)

    # Make pandas.read_csv raise FileNotFoundError
    monkeypatch.setattr(pd, "read_csv", lambda path: (_ for _ in ()).throw(FileNotFoundError()))

    with pytest.raises(FileNotFoundError):
        ml_model._load_sales_data("nonexistent.csv")


def test_prepare_with_no_rows_raises_runtime_error(monkeypatch):
    """If the loaded DataFrame has no rows, training should fail with RuntimeError."""
    empty_df = pd.DataFrame({"date": [], "sales": []})
    # Make _load_sales_data return an empty DataFrame
    monkeypatch.setattr(ml_model, "_load_sales_data", lambda path=None: empty_df)

    # Reset internal state
    ml_model._model = None
    ml_model._df = None

    with pytest.raises(RuntimeError):
        ml_model._prepare()
