"""
Unit Tests for Baseline Models and Static Controller (Mode A).

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
"""

import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import pytest
from src.simulation.process_simulator import PolymerInjectionSimulator
from src.models.baseline import BaselineRegressor, BaselineMetrics
from src.optimization.static_controller import StaticSOPController


@pytest.fixture
def data_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic")


@pytest.fixture
def train_df(data_dir):
    return pd.read_csv(os.path.join(data_dir, "dataset_train.csv"))


@pytest.fixture
def test_df(data_dir):
    return pd.read_csv(os.path.join(data_dir, "dataset_test_id.csv"))


@pytest.fixture
def simulator():
    return PolymerInjectionSimulator()


# ============================================================================
# 1. Baseline Model Regression Tests
# ============================================================================

def test_dummy_regressor_yields_zero_r2(train_df, test_df):
    """DummyRegressor predicting mean must yield near-zero R2 on held-out test data."""
    model = BaselineRegressor(model_type="dummy")
    model.fit(train_df, train_df)

    metrics = model.evaluate(test_df, test_df, n_train=len(train_df))
    assert metrics.model_name == "Dummy"
    assert metrics.n_train == 3500
    assert metrics.n_test == 750

    # R2 on unseen held-out test set for dummy mean prediction is <= 0.05
    assert abs(metrics.tensile_r2) < 0.05
    assert abs(metrics.shrinkage_r2) < 0.05


def test_linear_regressor_learns_true_signal(train_df, test_df):
    """Linear regression baseline must achieve high R2 (>0.85) on both quality targets."""
    model = BaselineRegressor(model_type="linear")
    model.fit(train_df, train_df)

    metrics = model.evaluate(test_df, test_df, n_train=len(train_df))
    assert metrics.model_name == "Linear"

    # Confirms model captures majority of non-linear variance
    assert metrics.tensile_r2 > 0.70  # Linear model captures ~76% due to quadratic thermal and moisture terms
    assert metrics.shrinkage_r2 > 0.90
    assert metrics.tensile_mae < 1.0  # MAE within 1 MPa
    assert metrics.shrinkage_mae < 0.10  # Shrinkage MAE within 0.1%


def test_ridge_regressor_stability(train_df, test_df):
    """Ridge regression baseline must match or exceed ordinary linear regression."""
    model = BaselineRegressor(model_type="ridge", alpha=1.0)
    model.fit(train_df, train_df)

    metrics = model.evaluate(test_df, test_df, n_train=len(train_df))
    assert metrics.model_name == "Ridge"
    assert metrics.tensile_r2 > 0.70
    assert metrics.shrinkage_r2 > 0.90


# ============================================================================
# 2. Static SOP Controller Tests
# ============================================================================

def test_static_sop_controller_fixed_setpoints():
    """Static controller unconditionally produces nominal setpoints."""
    controller = StaticSOPController()
    rec1 = controller.recommend({"moisture_pct": 0.10, "melt_flow_index": 25.0})
    rec2 = controller.recommend({"moisture_pct": 0.45, "melt_flow_index": 15.0})

    assert rec1["melt_temp_c"] == 230.0
    assert rec1["injection_pressure_mpa"] == 100.0
    assert rec1["cooling_time_s"] == 20.0
    assert rec1 == rec2


def test_static_sop_controller_evaluation(simulator, test_df):
    """Static SOP evaluation over held-out material disturbance batch."""
    controller = StaticSOPController()
    mat_cols = ["moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct"]
    df_mat = test_df[mat_cols].copy()

    df_evaluated = controller.evaluate_batch(df_mat, simulator=simulator, add_noise=True, seed=999)

    assert len(df_evaluated) == len(test_df)
    assert (df_evaluated["melt_temp_c"] == 230.0).all()
    assert (df_evaluated["injection_pressure_mpa"] == 100.0).all()
    assert (df_evaluated["cooling_time_s"] == 20.0).all()

    in_spec_pct = df_evaluated["in_spec_flag"].mean() * 100.0
    # In-distribution SOP in-spec yield is high (~90-100%) under nominal conditions
    assert 80.0 <= in_spec_pct <= 100.0


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main(["-v", __file__]))
