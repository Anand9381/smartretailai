from __future__ import annotations

from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def _ml_model():
    """Import pandas/sklearn-backed forecasting code only when an ML route is used."""
    import ml_model

    return ml_model


def predict_sales_lazy(day: Any) -> float:
    return _ml_model().predict_sales(day)


def detect_anomalies_lazy():
    return _ml_model().detect_anomalies()
