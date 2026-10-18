"""
Comparative Surrogate Benchmarking Engine.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 1)
"""

from __future__ import annotations
import os
import sys
import time
import platform
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
import joblib


@dataclass(frozen=True)
class SurrogateEvaluationResult:
    """Evaluation metrics for a surrogate model on a specific dataset partition."""
    model_name: str
    dataset_role: str
    n_samples: int
    tensile_mae: float
    tensile_rmse: float
    tensile_r2: float
    shrinkage_mae: float
    shrinkage_rmse: float
    shrinkage_r2: float
    mean_r2: float
    mean_rmse: float
    inference_latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SurrogateBenchmark:
    """
    Manages comparative benchmarking across parametric (Ridge) and non-parametric
    ensemble models (Decision Tree, Random Forest) for multi-output quality prediction.
    """

    FEATURE_COLS = [
        "moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct",
        "melt_temp_c", "injection_pressure_mpa", "cooling_time_s"
    ]
    TARGET_COLS = ["tensile_strength_mpa", "volumetric_shrinkage_pct"]

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.trained_pipelines: Dict[str, Pipeline] = {}
        self.tuning_records: Dict[str, Dict[str, Any]] = {}

    def _validate_data(self, df: pd.DataFrame, require_targets: bool = True) -> None:
        """Defensively check feature and target columns exist without NaNs."""
        missing_features = [col for col in self.FEATURE_COLS if col not in df.columns]
        if missing_features:
            raise KeyError(f"Missing required feature columns: {missing_features}")

        if df[self.FEATURE_COLS].isna().any().any():
            raise ValueError("Input features contain NaN or Inf values.")

        if require_targets:
            missing_targets = [col for col in self.TARGET_COLS if col not in df.columns]
            if missing_targets:
                raise KeyError(f"Missing required target columns: {missing_targets}")
            if df[self.TARGET_COLS].isna().any().any():
                raise ValueError("Target variables contain NaN or Inf values.")

    def evaluate_model(
        self,
        pipeline: Pipeline,
        df: pd.DataFrame,
        model_name: str,
        dataset_role: str
    ) -> SurrogateEvaluationResult:
        """
        Evaluate a trained surrogate pipeline on an evaluation dataset without target leakage.
        """
        self._validate_data(df, require_targets=True)

        X = df[self.FEATURE_COLS].to_numpy(dtype=float)
        y_true = df[self.TARGET_COLS].to_numpy(dtype=float)

        # Measure inference latency
        t0 = time.perf_counter()
        y_pred = pipeline.predict(X)
        latency_ms = ((time.perf_counter() - t0) / len(df)) * 1000.0

        # Target 0: Tensile Strength (MPa)
        tens_mae = float(mean_absolute_error(y_true[:, 0], y_pred[:, 0]))
        tens_rmse = float(root_mean_squared_error(y_true[:, 0], y_pred[:, 0]))
        tens_r2 = float(r2_score(y_true[:, 0], y_pred[:, 0]))

        # Target 1: Volumetric Shrinkage (%)
        shrink_mae = float(mean_absolute_error(y_true[:, 1], y_pred[:, 1]))
        shrink_rmse = float(root_mean_squared_error(y_true[:, 1], y_pred[:, 1]))
        shrink_r2 = float(r2_score(y_true[:, 1], y_pred[:, 1]))

        mean_r2 = float((tens_r2 + shrink_r2) / 2.0)
        mean_rmse = float((tens_rmse + shrink_rmse) / 2.0)

        return SurrogateEvaluationResult(
            model_name=model_name,
            dataset_role=dataset_role,
            n_samples=len(df),
            tensile_mae=tens_mae,
            tensile_rmse=tens_rmse,
            tensile_r2=tens_r2,
            shrinkage_mae=shrink_mae,
            shrinkage_rmse=shrink_rmse,
            shrinkage_r2=shrink_r2,
            mean_r2=mean_r2,
            mean_rmse=mean_rmse,
            inference_latency_ms=latency_ms
        )

    def tune_ridge(
        self,
        df_train: pd.DataFrame,
        df_val: pd.DataFrame,
        alphas: Optional[List[float]] = None
    ) -> Tuple[Pipeline, Dict[str, Any]]:
        """
        Train Ridge Regressor with validation-based alpha selection.
        """
        self._validate_data(df_train)
        self._validate_data(df_val)

        if alphas is None:
            alphas = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]

        X_train = df_train[self.FEATURE_COLS].to_numpy(dtype=float)
        y_train = df_train[self.TARGET_COLS].to_numpy(dtype=float)

        best_pipe = None
        best_alpha = None
        best_val_r2 = -float("inf")
        history = []

        for alpha in alphas:
            pipe = Pipeline([
                ("scaler", StandardScaler()),
                ("regressor", Ridge(alpha=alpha, random_state=self.random_state))
            ])
            pipe.fit(X_train, y_train)

            val_res = self.evaluate_model(pipe, df_val, "Ridge", "val")
            history.append({
                "alpha": alpha,
                "val_tensile_r2": val_res.tensile_r2,
                "val_shrinkage_r2": val_res.shrinkage_r2,
                "val_mean_r2": val_res.mean_r2
            })

            if val_res.mean_r2 > best_val_r2:
                best_val_r2 = val_res.mean_r2
                best_alpha = alpha
                best_pipe = pipe

        tuning_summary = {
            "model_type": "Ridge",
            "best_param": {"alpha": best_alpha},
            "best_val_mean_r2": best_val_r2,
            "grid_evaluated": history
        }
        self.trained_pipelines["Ridge"] = best_pipe
        self.tuning_records["Ridge"] = tuning_summary
        return best_pipe, tuning_summary

    def tune_decision_tree(
        self,
        df_train: pd.DataFrame,
        df_val: pd.DataFrame,
        max_depths: Optional[List[Optional[int]]] = None,
        min_samples_leafs: Optional[List[int]] = None
    ) -> Tuple[Pipeline, Dict[str, Any]]:
        """
        Train multi-output DecisionTreeRegressor with validation-based hyperparameter tuning.
        """
        self._validate_data(df_train)
        self._validate_data(df_val)

        if max_depths is None:
            max_depths = [4, 6, 8, 10, 12, 16, None]
        if min_samples_leafs is None:
            min_samples_leafs = [1, 2, 5, 10]

        X_train = df_train[self.FEATURE_COLS].to_numpy(dtype=float)
        y_train = df_train[self.TARGET_COLS].to_numpy(dtype=float)

        best_pipe = None
        best_params = {}
        best_val_r2 = -float("inf")
        history = []

        for md in max_depths:
            for msl in min_samples_leafs:
                pipe = Pipeline([
                    ("regressor", DecisionTreeRegressor(
                        max_depth=md,
                        min_samples_leaf=msl,
                        random_state=self.random_state
                    ))
                ])
                pipe.fit(X_train, y_train)

                val_res = self.evaluate_model(pipe, df_val, "DecisionTree", "val")
                history.append({
                    "max_depth": md,
                    "min_samples_leaf": msl,
                    "val_tensile_r2": val_res.tensile_r2,
                    "val_shrinkage_r2": val_res.shrinkage_r2,
                    "val_mean_r2": val_res.mean_r2
                })

                if val_res.mean_r2 > best_val_r2:
                    best_val_r2 = val_res.mean_r2
                    best_params = {"max_depth": md, "min_samples_leaf": msl}
                    best_pipe = pipe

        tuning_summary = {
            "model_type": "DecisionTree",
            "best_param": best_params,
            "best_val_mean_r2": best_val_r2,
            "grid_evaluated": history
        }
        self.trained_pipelines["DecisionTree"] = best_pipe
        self.tuning_records["DecisionTree"] = tuning_summary
        return best_pipe, tuning_summary

    def tune_random_forest(
        self,
        df_train: pd.DataFrame,
        df_val: pd.DataFrame,
        n_estimators: int = 100,
        max_depths: Optional[List[Optional[int]]] = None,
        min_samples_leafs: Optional[List[int]] = None
    ) -> Tuple[Pipeline, Dict[str, Any]]:
        """
        Train multi-output RandomForestRegressor with validation-based hyperparameter tuning.
        """
        self._validate_data(df_train)
        self._validate_data(df_val)

        if max_depths is None:
            max_depths = [6, 10, 14, 18, None]
        if min_samples_leafs is None:
            min_samples_leafs = [1, 2, 4]

        X_train = df_train[self.FEATURE_COLS].to_numpy(dtype=float)
        y_train = df_train[self.TARGET_COLS].to_numpy(dtype=float)

        best_pipe = None
        best_params = {}
        best_val_r2 = -float("inf")
        history = []

        for md in max_depths:
            for msl in min_samples_leafs:
                pipe = Pipeline([
                    ("regressor", RandomForestRegressor(
                        n_estimators=n_estimators,
                        max_depth=md,
                        min_samples_leaf=msl,
                        random_state=self.random_state,
                        n_jobs=-1
                    ))
                ])
                pipe.fit(X_train, y_train)

                val_res = self.evaluate_model(pipe, df_val, "RandomForest", "val")
                history.append({
                    "n_estimators": n_estimators,
                    "max_depth": md,
                    "min_samples_leaf": msl,
                    "val_tensile_r2": val_res.tensile_r2,
                    "val_shrinkage_r2": val_res.shrinkage_r2,
                    "val_mean_r2": val_res.mean_r2
                })

                if val_res.mean_r2 > best_val_r2:
                    best_val_r2 = val_res.mean_r2
                    best_params = {
                        "n_estimators": n_estimators,
                        "max_depth": md,
                        "min_samples_leaf": msl
                    }
                    best_pipe = pipe

        tuning_summary = {
            "model_type": "RandomForest",
            "best_param": best_params,
            "best_val_mean_r2": best_val_r2,
            "grid_evaluated": history
        }
        self.trained_pipelines["RandomForest"] = best_pipe
        self.tuning_records["RandomForest"] = tuning_summary
        return best_pipe, tuning_summary

    def run_full_benchmark(self, data_dir: str) -> Dict[str, Any]:
        """
        Execute full comparative benchmark across train, val, ID test, and 4 OOD stress datasets.
        """
        # Load datasets
        train_path = os.path.join(data_dir, "dataset_train.csv")
        val_path = os.path.join(data_dir, "dataset_val.csv")
        test_path = os.path.join(data_dir, "dataset_test_id.csv")

        ood_paths = {
            "ood_1_feedstock": os.path.join(data_dir, "dataset_ood_1_feedstock.csv"),
            "ood_2_thermal": os.path.join(data_dir, "dataset_ood_2_thermal.csv"),
            "ood_3_extrap": os.path.join(data_dir, "dataset_ood_3_extrap.csv"),
            "ood_4_sensor": os.path.join(data_dir, "dataset_ood_4_sensor.csv")
        }

        df_train = pd.read_csv(train_path)
        df_val = pd.read_csv(val_path)
        df_test_id = pd.read_csv(test_path)
        df_oods = {k: pd.read_csv(p) for k, p in ood_paths.items()}

        # 1. Baseline Reference Models (Dummy and Linear Regression)
        X_train = df_train[self.FEATURE_COLS].to_numpy(dtype=float)
        y_train = df_train[self.TARGET_COLS].to_numpy(dtype=float)

        pipe_dummy = Pipeline([("regressor", DummyRegressor(strategy="mean"))])
        pipe_dummy.fit(X_train, y_train)
        self.trained_pipelines["Dummy"] = pipe_dummy

        pipe_linear = Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", LinearRegression())
        ])
        pipe_linear.fit(X_train, y_train)
        self.trained_pipelines["LinearRegression"] = pipe_linear

        # 2. Tune Phase 3 Comparative Models
        self.tune_ridge(df_train, df_val)
        self.tune_decision_tree(df_train, df_val)
        self.tune_random_forest(df_train, df_val)

        # 3. Evaluate all models on held-out In-Distribution Test Set
        id_evaluations: List[Dict[str, Any]] = []
        for name, pipe in self.trained_pipelines.items():
            res = self.evaluate_model(pipe, df_test_id, name, "test_id")
            id_evaluations.append(res.to_dict())

        # 4. Evaluate all models on the 4 Out-of-Distribution stress sets
        ood_evaluations: Dict[str, List[Dict[str, Any]]] = {}
        for ood_name, df_ood in df_oods.items():
            ood_evaluations[ood_name] = []
            for name, pipe in self.trained_pipelines.items():
                res = self.evaluate_model(pipe, df_ood, name, ood_name)
                ood_evaluations[ood_name].append(res.to_dict())

        # Compile comprehensive benchmark payload
        payload = {
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "python_version": sys.version,
                "platform": platform.platform(),
                "sklearn_version": sklearn.__version__,
                "random_state": self.random_state,
                "n_train": len(df_train),
                "n_val": len(df_val),
                "n_test_id": len(df_test_id),
                "features": self.FEATURE_COLS,
                "targets": self.TARGET_COLS
            },
            "tuning_summary": self.tuning_records,
            "id_test_benchmarks": id_evaluations,
            "ood_benchmarks": ood_evaluations
        }

        return payload

    def save_models(self, output_dir: str) -> Dict[str, str]:
        """Serialize all trained pipelines to disk."""
        os.makedirs(output_dir, exist_ok=True)
        saved_paths = {}
        for name, pipe in self.trained_pipelines.items():
            filename = f"surrogate_{name.lower()}.joblib"
            path = os.path.join(output_dir, filename)
            joblib.dump(pipe, path)
            saved_paths[name] = path
        return saved_paths

    @staticmethod
    def load_model(path: str) -> Pipeline:
        """Load a serialized model pipeline from disk."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found at: {path}")
        return joblib.load(path)
