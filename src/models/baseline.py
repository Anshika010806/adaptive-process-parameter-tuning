"""
Baseline Surrogate Models for Multi-Output Quality Prediction.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score


@dataclass
class BaselineMetrics:
    """Quantitative performance metrics across dual quality targets."""
    model_name: str
    n_train: int
    n_test: int
    tensile_mae: float
    tensile_rmse: float
    tensile_r2: float
    shrinkage_mae: float
    shrinkage_rmse: float
    shrinkage_r2: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaselineRegressor:
    """
    Parametric and non-parametric baseline models predicting both
    Tensile Strength (MPa) and Volumetric Shrinkage (%) from process conditions.
    """

    FEATURE_COLS = [
        "moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct",
        "melt_temp_c", "injection_pressure_mpa", "cooling_time_s"
    ]
    TARGET_COLS = ["tensile_strength_mpa", "volumetric_shrinkage_pct"]

    def __init__(self, model_type: str = "linear", alpha: float = 1.0):
        self.model_type = model_type.lower()
        self.alpha = alpha
        self.pipeline: Optional[Pipeline] = None
        self._build_pipeline()

    def _build_pipeline(self) -> None:
        """Construct scikit-learn pipeline with scaling and estimator."""
        if self.model_type == "dummy":
            estimator = DummyRegressor(strategy="mean")
            self.pipeline = Pipeline([
                ("scaler", StandardScaler()),
                ("regressor", estimator)
            ])
        elif self.model_type == "linear":
            estimator = LinearRegression()
            self.pipeline = Pipeline([
                ("scaler", StandardScaler()),
                ("regressor", estimator)
            ])
        elif self.model_type == "ridge":
            estimator = Ridge(alpha=self.alpha)
            self.pipeline = Pipeline([
                ("scaler", StandardScaler()),
                ("regressor", estimator)
            ])
        else:
            raise ValueError(f"Unknown baseline model_type '{self.model_type}'. Choose 'dummy', 'linear', or 'ridge'.")

    def fit(self, X: pd.DataFrame, y: pd.DataFrame) -> BaselineRegressor:
        """Fit pipeline strictly on training data."""
        X_mat = X[self.FEATURE_COLS] if isinstance(X, pd.DataFrame) else X
        y_mat = y[self.TARGET_COLS] if isinstance(y, pd.DataFrame) else y
        self.pipeline.fit(X_mat, y_mat)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generate dual quality predictions: [tensile_pred, shrinkage_pred]."""
        if self.pipeline is None:
            raise RuntimeError("Model has not been fitted. Call fit() first.")
        X_mat = X[self.FEATURE_COLS] if isinstance(X, pd.DataFrame) else X
        return self.pipeline.predict(X_mat)

    def evaluate(
        self,
        X_test: pd.DataFrame,
        y_test: pd.DataFrame,
        n_train: int = 0
    ) -> BaselineMetrics:
        """Compute MAE, RMSE, and R2 across both quality targets."""
        preds = self.predict(X_test)
        actuals = y_test[self.TARGET_COLS].to_numpy(dtype=float) if isinstance(y_test, pd.DataFrame) else y_test

        tensile_actual = actuals[:, 0]
        tensile_pred = preds[:, 0]
        shrink_actual = actuals[:, 1]
        shrink_pred = preds[:, 1]

        t_mae = float(mean_absolute_error(tensile_actual, tensile_pred))
        t_rmse = float(root_mean_squared_error(tensile_actual, tensile_pred))
        t_r2 = float(r2_score(tensile_actual, tensile_pred))

        s_mae = float(mean_absolute_error(shrink_actual, shrink_pred))
        s_rmse = float(root_mean_squared_error(shrink_actual, shrink_pred))
        s_r2 = float(r2_score(shrink_actual, shrink_pred))

        return BaselineMetrics(
            model_name=self.model_type.capitalize(),
            n_train=n_train,
            n_test=len(X_test),
            tensile_mae=t_mae,
            tensile_rmse=t_rmse,
            tensile_r2=t_r2,
            shrinkage_mae=s_mae,
            shrinkage_rmse=s_rmse,
            shrinkage_r2=s_r2
        )
