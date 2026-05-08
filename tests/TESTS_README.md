# Tests - Simple Guide

This file explains in simple terms what each test in the `tests/` folder checks, how to run them, and what to expect.

## How to run

Activate your virtual environment and run the test suite from the project root:

```bash
pytest -q
```

Or run a single file:

```bash
pytest -q tests/test_ml.py
pytest -q tests/test_utils.py
```

## Purpose of the tests

- `test_ml.py`
  - Tests the main ML functions in `ml_model.py`:
    - `predict_sales` should return a float for valid inputs.
    - `detect_anomalies` should flag obvious outliers in sales data.
  - Uses small, easy-to-read pandas DataFrames and mocking so it doesn't need a real DB.

- `test_utils.py`
  - Verifies the logging helper returns a usable logger object.
  - Very simple – just ensures logging is configured by the project code.

- `test_ml_errors.py`
  - Tests error handling in `ml_model.py`:
    - Missing CSV raises FileNotFoundError when MongoDB is not available.
    - Preparing with an empty DataFrame raises RuntimeError (no data to train).

## Notes for reviewers (in simple terms)

- Tests are written to be easy to understand and modify. Each test has a short comment explaining the intent.
- Tests avoid external dependencies where possible (we mock DB/CSV access or skip live SDK tests).
- If you add tests that call external services (Azure, DB, etc.), either mock those services or add guards so the tests skip when the SDK is not installed.

## Troubleshooting

- If pytest reports an `ImportError` for `azure` when running the full suite, install the Azure SDK or run tests only in `tests/` (the `services/test_search.py` module is guarded to skip when Azure is missing).
- If pytest seems to pick up a script at project root named like a test (for example `test_ml.py`), move it to `scripts/` (we already moved the smoke test to `scripts/smoke_test_ml.py`).

## Adding a new test

1. Create a file named `tests/test_myfeature.py`.
2. Keep the tests small and focused: one assertion per logical outcome if possible.
3. Use `monkeypatch` or `unittest.mock.patch` to replace external calls (DB, HTTP, file reads).
4. Run `pytest -q tests/test_myfeature.py` to verify.

---
If anything here is unclear, tell me which test you'd like explained in even simpler words and I will update this file.
