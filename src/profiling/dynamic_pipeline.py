"""
Dynamic Pipeline Builder for Arbitrary Schemas (Mode B).

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

from .schema_validator import SchemaMapping, ValidationResult


@dataclass
class EvaluationMetrics:
    """Quantitative performance metrics from evaluated pipeline."""
    model_name: str
    target_name: str
    n_train: int
    n_test: int
    mae: float
    rmse: float
    r2: float
    y_test_mean: float
    y_test_std: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DynamicPipelineBuilder:
    """
    Constructs leakage-free, dynamically configured preprocessing and regression
    pipelines based on confirmed schema validation results.
    """

    def __init__(self, validation_result: ValidationResult):
        if not validation_result.is_valid:
            raise ValueError(f"Cannot build pipeline from invalid schema: {validation_result.errors}")
        self.validation = validation_result
        self.numeric_cols = validation_result.numeric_features
        self.categorical_cols = validation_result.categorical_features

    def build_preprocessor(self) -> ColumnTransformer:
        """
        Build scikit-learn ColumnTransformer dynamically.
        Numeric: median imputation + standard scaling.
        Categorical: mode imputation + one-hot encoding with handle_unknown='ignore'.
        """
        transformers = []

        if self.numeric_cols:
            num_pipe = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ])
            transformers.append(("num", num_pipe, self.numeric_cols))

        if self.categorical_cols:
            cat_pipe = Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ])
            transformers.append(("cat", cat_pipe, self.categorical_cols))

        return ColumnTransformer(transformers=transformers, remainder="drop")

    def build_pipeline(self, regressor: Optional[Any] = None) -> Pipeline:
        """
        Assemble the full end-to-end pipeline with an estimator.
        Defaults to Ridge regression if no estimator is supplied.
        """
        preprocessor = self.build_preprocessor()
        model = regressor if regressor is not None else Ridge(alpha=1.0)
        return Pipeline([
            ("preprocessor", preprocessor),
            ("regressor", model),
        ])

    def fit_and_evaluate(
        self,
        df: pd.DataFrame,
        mapping: SchemaMapping,
        regressor: Optional[Any] = None,
        model_name: str = "Ridge",
        test_size: float = 0.20,
        random_state: int = 42
    ) -> Tuple[Pipeline, EvaluationMetrics, pd.DataFrame]:
        """
        Execute train/test split, fit pipeline exclusively on train fold (zero leakage),
        and evaluate performance on held-out test fold.
        """
        target = mapping.target_column
        features = self.numeric_cols + self.categorical_cols

        # Filter out rows with missing target
        clean_df = df.dropna(subset=[target]).copy()

        X = clean_df[features]
        y = clean_df[target].to_numpy(dtype=float)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        pipeline = self.build_pipeline(regressor=regressor)
        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)

        mae = float(mean_absolute_error(y_test, y_pred))
        rmse = float(root_mean_squared_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred)) if len(np.unique(y_test)) > 1 else 0.0

        metrics = EvaluationMetrics(
            model_name=model_name,
            target_name=target,
            n_train=len(X_train),
            n_test=len(X_test),
            mae=mae,
            rmse=rmse,
            r2=r2,
            y_test_mean=float(np.mean(y_test)),
            y_test_std=float(np.std(y_test, ddof=1)) if len(y_test) > 1 else 0.0,
        )

        # Build comparison preview DataFrame
        eval_df = pd.DataFrame({
            "actual": y_test,
            "predicted": y_pred,
            "residual": y_test - y_pred,
            "abs_error": np.abs(y_test - y_pred),
        }, index=X_test.index)

        return pipeline, metrics, eval_df
