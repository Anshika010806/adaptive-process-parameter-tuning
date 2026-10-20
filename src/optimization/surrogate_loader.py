"""
Surrogate Model Loader and Training Interface for Gate 2.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 2)
"""

from __future__ import annotations
import os
import json
from typing import Optional, Dict, Any
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
import joblib

FEATURE_COLS = [
    "moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct",
    "melt_temp_c", "injection_pressure_mpa", "cooling_time_s"
]
TARGET_COLS = ["tensile_strength_mpa", "volumetric_shrinkage_pct"]


def get_default_model_params(model_type: str) -> Dict[str, Any]:
    """Retrieve verified Gate 1 hyperparameters."""
    normalized = model_type.strip().lower()
    if normalized in ["rf", "randomforest", "random_forest"]:
        return {
            "model_type": "RandomForest",
            "n_estimators": 100,
            "max_depth": 18,
            "min_samples_leaf": 1
        }
    elif normalized in ["ridge", "ridge_regression"]:
        return {
            "model_type": "Ridge",
            "alpha": 10.0
        }
    elif normalized in ["dt", "decisiontree", "decision_tree"]:
        return {
            "model_type": "DecisionTree",
            "max_depth": 16,
            "min_samples_leaf": 5
        }
    else:
        raise ValueError(f"Unsupported model type '{model_type}'. Choose from ['RandomForest', 'Ridge', 'DecisionTree'].")


def build_pipeline(model_type: str, random_state: int = 42) -> Pipeline:
    """Construct sklearn pipeline with preprocessing matching Gate 1 specification."""
    params = get_default_model_params(model_type)
    m_type = params["model_type"]

    if m_type == "RandomForest":
        return Pipeline([
            ("regressor", RandomForestRegressor(
                n_estimators=params["n_estimators"],
                max_depth=params["max_depth"],
                min_samples_leaf=params["min_samples_leaf"],
                random_state=random_state,
                n_jobs=-1
            ))
        ])
    elif m_type == "Ridge":
        return Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", Ridge(alpha=params["alpha"], random_state=random_state))
        ])
    elif m_type == "DecisionTree":
        return Pipeline([
            ("regressor", DecisionTreeRegressor(
                max_depth=params["max_depth"],
                min_samples_leaf=params["min_samples_leaf"],
                random_state=random_state
            ))
        ])
    raise ValueError(f"Unknown model type: {m_type}")


def load_or_train_surrogate(
    model_name: str = "RandomForest",
    data_dir: Optional[str] = None,
    models_dir: Optional[str] = None,
    random_state: int = 42,
    force_retrain: bool = False
) -> Pipeline:
    """
    Load serialized Gate 1 surrogate model, or reproducibly train on dataset_train.csv.

    Crucial Guardrails:
    - Trains exclusively on dataset_train.csv (training data only).
    - Never accesses or fits on held-out test (dataset_test_id.csv) or OOD stress datasets.
    - Preserves Gate 1 validated hyperparameters.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if data_dir is None:
        data_dir = os.path.join(base_dir, "data", "synthetic")
    if models_dir is None:
        models_dir = os.path.join(base_dir, "models")

    os.makedirs(models_dir, exist_ok=True)
    canonical_name = get_default_model_params(model_name)["model_type"]
    model_file = f"surrogate_{canonical_name.lower()}.joblib"
    model_path = os.path.join(models_dir, model_file)

    if os.path.exists(model_path) and not force_retrain:
        try:
            pipe = joblib.load(model_path)
            return pipe
        except Exception as e:
            print(f"[Warning] Failed to load cached model at {model_path}: {e}. Retraining on training data...")

    # Load training data ONLY
    train_csv = os.path.join(data_dir, "dataset_train.csv")
    if not os.path.exists(train_csv):
        from src.simulation.data_generator import DataGenerator
        generator = DataGenerator()
        generator.generate_and_save_all(data_dir)

    df_train = pd.read_csv(train_csv)
    missing_cols = [c for c in FEATURE_COLS + TARGET_COLS if c not in df_train.columns]
    if missing_cols:
        raise KeyError(f"Training dataset {train_csv} is missing columns: {missing_cols}")

    X_train = df_train[FEATURE_COLS].to_numpy(dtype=float)
    y_train = df_train[TARGET_COLS].to_numpy(dtype=float)

    pipe = build_pipeline(canonical_name, random_state=random_state)
    pipe.fit(X_train, y_train)

    # Persist serialized artifact
    joblib.dump(pipe, model_path)
    return pipe
