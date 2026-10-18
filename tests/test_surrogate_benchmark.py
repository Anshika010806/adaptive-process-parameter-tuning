"""
Unit tests for Comparative Surrogate Benchmarking Engine.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 1)
"""

import os
import sys
import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.surrogate_benchmark import SurrogateBenchmark, SurrogateEvaluationResult


@pytest.fixture
def synthetic_splits():
    """Load or generate minimal training, validation, and test splits for testing."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic")
    train_path = os.path.join(data_dir, "dataset_train.csv")
    val_path = os.path.join(data_dir, "dataset_val.csv")
    test_path = os.path.join(data_dir, "dataset_test_id.csv")

    if os.path.exists(train_path) and os.path.exists(val_path) and os.path.exists(test_path):
        df_train = pd.read_csv(train_path).head(300)
        df_val = pd.read_csv(val_path).head(100)
        df_test = pd.read_csv(test_path).head(100)
    else:
        # Fallback dummy dataframe matching exact schema
        cols = SurrogateBenchmark.FEATURE_COLS + SurrogateBenchmark.TARGET_COLS
        df_train = pd.DataFrame(np.random.randn(300, len(cols)), columns=cols)
        df_val = pd.DataFrame(np.random.randn(100, len(cols)), columns=cols)
        df_test = pd.DataFrame(np.random.randn(100, len(cols)), columns=cols)

    return df_train, df_val, df_test


def test_leakage_prevention(synthetic_splits):
    """Verify that transformers are fit exclusively on training data and not modified by test evaluations."""
    df_train, df_val, df_test = synthetic_splits
    benchmarker = SurrogateBenchmark(random_state=42)

    pipe, _ = benchmarker.tune_ridge(df_train, df_val, alphas=[1.0])
    scaler = pipe.named_steps["scaler"]

    # Verify scaler mean matches training set exclusively
    expected_means = df_train[benchmarker.FEATURE_COLS].mean().to_numpy()
    np.testing.assert_allclose(scaler.mean_, expected_means, rtol=1e-4)

    # Evaluate on test set
    benchmarker.evaluate_model(pipe, df_test, "Ridge", "test")

    # Verify scaler parameters did NOT change after test evaluation
    np.testing.assert_allclose(scaler.mean_, expected_means, rtol=1e-4)


def test_target_handling_multi_output(synthetic_splits):
    """Verify that models output dual predictions with correct shape and aligned targets."""
    df_train, df_val, df_test = synthetic_splits
    benchmarker = SurrogateBenchmark(random_state=42)

    pipe_tree, _ = benchmarker.tune_decision_tree(df_train, df_val, max_depths=[4], min_samples_leafs=[2])
    X_test = df_test[benchmarker.FEATURE_COLS].to_numpy()
    preds = pipe_tree.predict(X_test)

    assert preds.shape == (len(df_test), 2)
    assert not np.isnan(preds).any()
    assert not np.isinf(preds).any()


def test_reproducibility(synthetic_splits):
    """Verify that identical random seeds yield identical model parameters and predictions."""
    df_train, df_val, df_test = synthetic_splits

    benchmarker_1 = SurrogateBenchmark(random_state=123)
    benchmarker_2 = SurrogateBenchmark(random_state=123)

    pipe_rf1, _ = benchmarker_1.tune_random_forest(
        df_train, df_val, n_estimators=20, max_depths=[6], min_samples_leafs=[1]
    )
    pipe_rf2, _ = benchmarker_2.tune_random_forest(
        df_train, df_val, n_estimators=20, max_depths=[6], min_samples_leafs=[1]
    )

    X_test = df_test[SurrogateBenchmark.FEATURE_COLS].to_numpy()
    preds1 = pipe_rf1.predict(X_test)
    preds2 = pipe_rf2.predict(X_test)

    np.testing.assert_allclose(preds1, preds2, rtol=1e-6)


def test_metric_calculation_accuracy(synthetic_splits):
    """Verify that MAE, RMSE, and R2 calculations match numpy ground truth."""
    df_train, df_val, df_test = synthetic_splits
    benchmarker = SurrogateBenchmark(random_state=42)

    pipe, _ = benchmarker.tune_ridge(df_train, df_val, alphas=[1.0])
    res = benchmarker.evaluate_model(pipe, df_test, "Ridge", "test")

    y_true = df_test[benchmarker.TARGET_COLS].to_numpy()
    y_pred = pipe.predict(df_test[benchmarker.FEATURE_COLS].to_numpy())

    manual_tens_mae = np.mean(np.abs(y_true[:, 0] - y_pred[:, 0]))
    manual_tens_rmse = np.sqrt(np.mean((y_true[:, 0] - y_pred[:, 0]) ** 2))
    manual_tens_r2 = 1.0 - (np.sum((y_true[:, 0] - y_pred[:, 0]) ** 2) / np.sum((y_true[:, 0] - np.mean(y_true[:, 0])) ** 2))

    assert pytest.approx(res.tensile_mae, rel=1e-4) == manual_tens_mae
    assert pytest.approx(res.tensile_rmse, rel=1e-4) == manual_tens_rmse
    assert pytest.approx(res.tensile_r2, rel=1e-4) == manual_tens_r2


def test_input_validation_catches_missing_columns_or_nans():
    """Verify defensive exceptions on missing features or corrupted values."""
    benchmarker = SurrogateBenchmark(random_state=42)

    # Missing column
    df_bad = pd.DataFrame({"moisture_pct": [0.15, 0.20]})
    with pytest.raises(KeyError, match="Missing required feature columns"):
        benchmarker.evaluate_model(None, df_bad, "Dummy", "test")

    # NaN in features
    cols = SurrogateBenchmark.FEATURE_COLS + SurrogateBenchmark.TARGET_COLS
    df_nan = pd.DataFrame(np.ones((5, len(cols))), columns=cols)
    df_nan.loc[0, "melt_temp_c"] = np.nan
    with pytest.raises(ValueError, match="Input features contain NaN or Inf"):
        benchmarker.evaluate_model(None, df_nan, "Dummy", "test")


def test_model_serialization_roundtrip(synthetic_splits, tmp_path):
    """Verify that models saved via joblib produce identical predictions upon loading."""
    df_train, df_val, df_test = synthetic_splits
    benchmarker = SurrogateBenchmark(random_state=42)

    benchmarker.tune_decision_tree(df_train, df_val, max_depths=[5], min_samples_leafs=[2])
    saved_paths = benchmarker.save_models(str(tmp_path))

    assert "DecisionTree" in saved_paths
    loaded_pipe = SurrogateBenchmark.load_model(saved_paths["DecisionTree"])

    X_test = df_test[benchmarker.FEATURE_COLS].to_numpy()
    orig_preds = benchmarker.trained_pipelines["DecisionTree"].predict(X_test)
    loaded_preds = loaded_pipe.predict(X_test)

    np.testing.assert_allclose(orig_preds, loaded_preds, rtol=1e-6)
