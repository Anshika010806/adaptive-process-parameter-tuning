"""
Unit tests for Adaptive Process Parameter Tuner.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 2 & Gate 4)
"""

import os
import sys
import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulation.process_simulator import PolymerInjectionSimulator
from src.optimization.adaptive_tuner import AdaptiveProcessTuner, TuningRecommendation


@pytest.fixture
def trained_surrogate():
    """Build and train a fast lightweight surrogate for testing."""
    # Synthetic dataset matching exact 7 feature columns and 2 target columns
    feature_cols = AdaptiveProcessTuner.FEATURE_COLS
    target_cols = ["tensile_strength_mpa", "volumetric_shrinkage_pct"]

    rng = np.random.default_rng(42)
    N = 200
    X_mat = pd.DataFrame({
        "moisture_pct": rng.uniform(0.08, 0.35, N),
        "melt_flow_index": rng.uniform(16.0, 26.0, N),
        "ambient_temp_c": rng.uniform(20.0, 28.0, N),
        "recycled_pct": rng.uniform(15.0, 35.0, N),
        "melt_temp_c": rng.uniform(210.0, 250.0, N),
        "injection_pressure_mpa": rng.uniform(75.0, 135.0, N),
        "cooling_time_s": rng.uniform(14.0, 28.0, N)
    })

    sim = PolymerInjectionSimulator()
    df_sim = sim.evaluate_batch(X_mat, add_noise=False)

    pipe = Pipeline([
        ("regressor", RandomForestRegressor(n_estimators=10, max_depth=6, random_state=42))
    ])
    pipe.fit(X_mat[feature_cols].to_numpy(), df_sim[target_cols].to_numpy())
    return pipe


def test_actuator_bounds_strictly_enforced(trained_surrogate):
    """Verify that recommended setpoints never exceed physical machine actuator bounds."""
    tuner = AdaptiveProcessTuner(surrogate_pipeline=trained_surrogate)

    rng = np.random.default_rng(101)
    for _ in range(25):
        m = rng.uniform(0.05, 0.45)
        mfi = rng.uniform(14.0, 30.0)
        t_amb = rng.uniform(18.0, 32.0)
        rec_pct = rng.uniform(10.0, 40.0)

        rec = tuner.optimize_cycle(m, mfi, t_amb, rec_pct)

        assert tuner.bounds["melt_temp_c"][0] <= rec.melt_temp_c <= tuner.bounds["melt_temp_c"][1]
        assert tuner.bounds["injection_pressure_mpa"][0] <= rec.injection_pressure_mpa <= tuner.bounds["injection_pressure_mpa"][1]
        assert tuner.bounds["cooling_time_s"][0] <= rec.cooling_time_s <= tuner.bounds["cooling_time_s"][1]


def test_infeasibility_detection_on_extreme_moisture(trained_surrogate):
    """Verify that extreme uncompensable moisture (M > 0.55 wt%) is flagged as INFEASIBLE and uses fallback."""
    tuner = AdaptiveProcessTuner(surrogate_pipeline=trained_surrogate)

    rec = tuner.optimize_cycle(
        moisture_pct=0.68,
        melt_flow_index=22.0,
        ambient_temp_c=24.0,
        recycled_pct=25.0
    )

    assert rec.is_feasible is False
    assert rec.status == "INFEASIBLE"
    assert "cannot be compensated" in rec.message.lower() or "exceeds" in rec.message.lower()
    # Check fallback setpoints
    assert rec.melt_temp_c == tuner.sop_defaults["melt_temp_c"]
    assert rec.injection_pressure_mpa == tuner.sop_defaults["injection_pressure_mpa"]


def test_optimizer_handles_tree_surrogate_without_gradient(trained_surrogate):
    """Verify derivative-free multi-start finds a feasible or optimal recommendation."""
    tuner = AdaptiveProcessTuner(surrogate_pipeline=trained_surrogate)

    rec = tuner.optimize_cycle(
        moisture_pct=0.15,
        melt_flow_index=22.0,
        ambient_temp_c=24.0,
        recycled_pct=25.0
    )

    assert rec.status in ["OPTIMAL", "SUBOPTIMAL"]
    assert rec.is_feasible is True
    assert 40.0 <= rec.predicted_tensile_mpa <= 60.0
    assert 0.50 <= rec.predicted_shrinkage_pct <= 2.0


def test_true_simulator_closed_loop_evaluation(trained_surrogate):
    """Verify recommended setpoints execute cleanly in independent true simulator."""
    tuner = AdaptiveProcessTuner(surrogate_pipeline=trained_surrogate)
    sim = PolymerInjectionSimulator()

    rec = tuner.optimize_cycle(
        moisture_pct=0.20,
        melt_flow_index=20.0,
        ambient_temp_c=25.0,
        recycled_pct=30.0
    )

    realized = sim.evaluate_single(
        moisture_pct=0.20,
        melt_flow_index=20.0,
        ambient_temp_c=25.0,
        recycled_pct=30.0,
        melt_temp_c=rec.melt_temp_c,
        injection_pressure_mpa=rec.injection_pressure_mpa,
        cooling_time_s=rec.cooling_time_s,
        add_noise=False
    )

    assert realized.tensile_strength_mpa > 45.0
    assert realized.volumetric_shrinkage_pct > 0.0
    assert realized.energy_kwh > 0.0


def test_batch_tuning_dataframe(trained_surrogate):
    """Verify tune_batch processes an entire material stream and returns expected columns."""
    tuner = AdaptiveProcessTuner(surrogate_pipeline=trained_surrogate)

    df_mat = pd.DataFrame({
        "moisture_pct": [0.12, 0.22, 0.70],
        "melt_flow_index": [24.0, 18.0, 15.0],
        "ambient_temp_c": [22.0, 26.0, 25.0],
        "recycled_pct": [20.0, 30.0, 35.0]
    })

    df_tuned = tuner.tune_batch(df_mat)

    assert len(df_tuned) == 3
    for col in ["melt_temp_c", "injection_pressure_mpa", "cooling_time_s", "status", "is_feasible"]:
        assert col in df_tuned.columns

    # Third row should be flagged as infeasible
    assert df_tuned.loc[2, "is_feasible"] == False
    assert df_tuned.loc[2, "status"] == "INFEASIBLE"


def test_input_validation_catches_missing_material_cols(trained_surrogate):
    """Verify KeyError is raised when DataFrame lacks required material columns."""
    tuner = AdaptiveProcessTuner(surrogate_pipeline=trained_surrogate)

    df_bad = pd.DataFrame({"moisture_pct": [0.15], "ambient_temp_c": [24.0]})
    with pytest.raises(KeyError, match="missing required material columns"):
        tuner.tune_batch(df_bad)
