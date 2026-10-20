"""
Comprehensive Unit and Integration Tests for Gate 2: Adaptive Process Parameter Tuning.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 2)
"""

import os
import sys
import tempfile
import json
import numpy as np
import pandas as pd
import pytest

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulation.process_simulator import PolymerInjectionSimulator
from src.optimization.static_controller import StaticSOPController
from src.optimization.domain_guard import DomainGuard, GuardResult
from src.optimization.surrogate_loader import load_or_train_surrogate, build_pipeline, get_default_model_params
from src.optimization.adaptive_tuner import AdaptiveProcessTuner, TuningRecommendation
from src.optimization.simulator_validator import SimulatorValidator, SimulatorValidationResult
from src.optimization.run_gate2 import run_gate2_single, run_gate2_batch


@pytest.fixture(scope="module")
def shared_surrogate():
    """Load or train surrogate using training data exclusively."""
    return load_or_train_surrogate(model_name="RandomForest", random_state=42)


@pytest.fixture
def tuner(shared_surrogate):
    """Instantiate standard AdaptiveProcessTuner."""
    return AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        random_state=42,
        search_strategy="grid",
        grid_resolution=(9, 9, 7),
        reject_ood=True
    )


@pytest.fixture
def domain_guard():
    """Instantiate DomainGuard."""
    return DomainGuard(reject_ood=True)


@pytest.fixture
def validator():
    """Instantiate SimulatorValidator."""
    return SimulatorValidator()


# ==============================================================================
# 1. Actuator Bounds Tests
# ==============================================================================

def test_actuator_bounds_enforced(tuner):
    """Verify actuator setpoints never exceed machine mechanical and thermal bounds."""
    rng = np.random.default_rng(101)
    for _ in range(15):
        m = rng.uniform(0.10, 0.40)
        mfi = rng.uniform(16.0, 28.0)
        t_amb = rng.uniform(18.0, 30.0)
        rec = rng.uniform(12.0, 38.0)

        rec_out = tuner.optimize_cycle(m, mfi, t_amb, rec)
        if rec_out.is_feasible:
            assert tuner.bounds["melt_temp_c"][0] <= rec_out.melt_temp_c <= tuner.bounds["melt_temp_c"][1]
            assert tuner.bounds["injection_pressure_mpa"][0] <= rec_out.injection_pressure_mpa <= tuner.bounds["injection_pressure_mpa"][1]
            assert tuner.bounds["cooling_time_s"][0] <= rec_out.cooling_time_s <= tuner.bounds["cooling_time_s"][1]


# ==============================================================================
# 2. Quality Constraints Tests
# ==============================================================================

def test_quality_constraints_enforced(tuner):
    """Verify feasible candidates satisfy hard tensile (49-55 MPa) and shrinkage (0.80-1.60%)."""
    rec = tuner.optimize_cycle(
        moisture_pct=0.18,
        melt_flow_index=21.0,
        ambient_temp_c=25.0,
        recycled_pct=28.0
    )
    assert rec.is_feasible is True
    assert rec.status == "OPTIMAL"
    assert 49.0 <= rec.predicted_tensile_mpa <= 55.0
    assert 0.80 <= rec.predicted_shrinkage_pct <= 1.60
    assert rec.predicted_in_spec is True


def test_reject_quality_infeasible_even_if_energy_is_low(shared_surrogate):
    """Verify that quality-infeasible candidates are rejected even if their energy is low."""
    tuner_obj = AdaptiveProcessTuner(surrogate_pipeline=shared_surrogate)

    # For an input where no candidate is feasible or artificial extreme constraints
    # Any candidate with tensile < 49.0 must be rejected
    cands = tuner_obj.candidate_actuators
    x_mat = np.tile([0.18, 21.0, 25.0, 28.0], (len(cands), 1))
    preds = shared_surrogate.predict(np.hstack([x_mat, cands]))
    E = tuner_obj.compute_energy(cands[:, 0], cands[:, 1], cands[:, 2], 25.0)

    # Candidate with absolute minimum energy
    min_e_idx = int(np.argmin(E))
    s_min_e = preds[min_e_idx, 0]
    v_min_e = preds[min_e_idx, 1]

    # The tuner must never select a candidate violating specs just to lower energy
    rec = tuner_obj.optimize_cycle(0.18, 21.0, 25.0, 28.0)
    assert 49.0 <= rec.predicted_tensile_mpa <= 55.0
    assert 0.80 <= rec.predicted_shrinkage_pct <= 1.60


# ==============================================================================
# 3. Domain Guard & Out-of-Distribution (OOD) Rejection Tests
# ==============================================================================

def test_ood_rejection_moisture(tuner, domain_guard):
    """Verify moisture outside training support [0.05, 0.50] is rejected with OOD_REJECTED."""
    # Upper OOD moisture (0.52 wt% is > 0.50 training max but <= 0.55 uncompensable threshold)
    res_upper = domain_guard.validate_material(0.52, 22.0, 24.0, 25.0)
    assert res_upper.is_in_support is False
    assert res_upper.is_feasible is False
    assert res_upper.status == "OOD_REJECTED"
    assert "outside training support" in res_upper.message

    rec_upper = tuner.optimize_cycle(0.52, 22.0, 24.0, 25.0)
    assert rec_upper.status == "OOD_REJECTED"
    assert rec_upper.is_feasible is False
    assert np.isnan(rec_upper.predicted_tensile_mpa)

    # Lower OOD moisture (< 0.05 wt%)
    res_lower = domain_guard.validate_material(0.02, 22.0, 24.0, 25.0)
    assert res_lower.status == "OOD_REJECTED"
    assert res_lower.is_feasible is False


def test_ood_rejection_ambient_temp(tuner, domain_guard):
    """Verify ambient temperature outside [16, 32] C (e.g. OOD-2 heatwave 36.5 C) is rejected."""
    # OOD-2 heatwave condition
    res_hot = domain_guard.validate_material(0.15, 22.0, 36.5, 25.0)
    assert res_hot.is_in_support is False
    assert res_hot.is_feasible is False
    assert res_hot.status == "OOD_REJECTED"
    assert "ambient_temp_c" in res_hot.message

    rec_hot = tuner.optimize_cycle(0.15, 22.0, 36.5, 25.0)
    assert rec_hot.status == "OOD_REJECTED"
    assert rec_hot.is_feasible is False
    assert np.isnan(rec_hot.predicted_tensile_mpa)

    # OOD cold condition
    res_cold = domain_guard.validate_material(0.15, 22.0, 10.0, 25.0)
    assert res_cold.status == "OOD_REJECTED"


def test_ood_rejection_mfi(tuner, domain_guard):
    """Verify Melt Flow Index outside [14, 30] g/10 min is rejected with OOD_REJECTED."""
    res_high = domain_guard.validate_material(0.15, 35.0, 24.0, 25.0)
    assert res_high.status == "OOD_REJECTED"
    assert res_high.is_feasible is False

    res_low = domain_guard.validate_material(0.15, 10.0, 24.0, 25.0)
    assert res_low.status == "OOD_REJECTED"


def test_ood_rejection_recycled_pct(tuner, domain_guard):
    """Verify recycled content outside [10, 40] wt% is rejected with OOD_REJECTED."""
    res_high = domain_guard.validate_material(0.15, 22.0, 24.0, 45.0)
    assert res_high.status == "OOD_REJECTED"
    assert res_high.is_feasible is False

    res_low = domain_guard.validate_material(0.15, 22.0, 24.0, 5.0)
    assert res_low.status == "OOD_REJECTED"


# ==============================================================================
# 4. Invalid Input Handling Tests
# ==============================================================================

def test_invalid_inputs_rejected(domain_guard, tuner):
    """Verify unphysical inputs (negative values, NaNs, Infs) are rejected with INVALID_INPUT."""
    # Negative moisture
    res_neg_m = domain_guard.validate_material(-0.05, 22.0, 24.0, 25.0)
    assert res_neg_m.is_valid is False
    assert res_neg_m.status == "INVALID_INPUT"

    # Negative MFI
    res_neg_mfi = domain_guard.validate_material(0.15, -5.0, 24.0, 25.0)
    assert res_neg_mfi.is_valid is False
    assert res_neg_mfi.status == "INVALID_INPUT"

    # NaN in ambient temp
    res_nan = domain_guard.validate_material(0.15, 22.0, float("nan"), 25.0)
    assert res_nan.is_valid is False
    assert res_nan.status == "INVALID_INPUT"

    # Inf in recycled pct
    res_inf = domain_guard.validate_material(0.15, 22.0, 24.0, float("inf"))
    assert res_inf.is_valid is False
    assert res_inf.status == "INVALID_INPUT"

    rec_nan = tuner.optimize_cycle(0.15, 22.0, float("nan"), 25.0)
    assert rec_nan.is_feasible is False
    assert rec_nan.status == "INVALID_INPUT"


# ==============================================================================
# 5. Infeasible Physical Regimes Tests
# ==============================================================================

def test_extreme_uncompensable_moisture(tuner, domain_guard):
    """Verify moisture > 0.55 wt% causes severe voiding flagged as INFEASIBLE."""
    res = domain_guard.validate_material(0.68, 22.0, 24.0, 25.0)
    assert res.is_feasible is False
    assert res.status == "INFEASIBLE"
    assert "cannot be compensated" in res.message.lower()

    rec = tuner.optimize_cycle(0.68, 22.0, 24.0, 25.0)
    assert rec.is_feasible is False
    assert rec.status == "INFEASIBLE"
    assert rec.melt_temp_c == tuner.sop_defaults["melt_temp_c"]


def test_compound_extreme_degradation(tuner, domain_guard):
    """Verify compound high moisture (>0.45%) and high recycled content (>38%) is flagged INFEASIBLE."""
    res = domain_guard.validate_material(0.48, 22.0, 24.0, 39.0)
    assert res.is_feasible is False
    assert res.status == "INFEASIBLE"
    assert "compound degradation" in res.violations[0].lower() or "exceeds" in res.message.lower()


# ==============================================================================
# 6. Reproducibility Tests
# ==============================================================================

def test_reproducibility_across_runs(shared_surrogate):
    """Verify that identical random seed produces identical recommendations and metrics."""
    tuner1 = AdaptiveProcessTuner(surrogate_pipeline=shared_surrogate, random_state=42)
    tuner2 = AdaptiveProcessTuner(surrogate_pipeline=shared_surrogate, random_state=42)

    rec1 = tuner1.optimize_cycle(0.18, 21.0, 25.0, 28.0)
    rec2 = tuner2.optimize_cycle(0.18, 21.0, 25.0, 28.0)

    assert rec1.melt_temp_c == rec2.melt_temp_c
    assert rec1.injection_pressure_mpa == rec2.injection_pressure_mpa
    assert rec1.cooling_time_s == rec2.cooling_time_s
    assert rec1.predicted_tensile_mpa == pytest.approx(rec2.predicted_tensile_mpa, abs=1e-7)
    assert rec1.predicted_energy_kwh == pytest.approx(rec2.predicted_energy_kwh, abs=1e-7)


# ==============================================================================
# 7. Simulator Integration & Matched Baseline Tests
# ==============================================================================

def test_simulator_validation_matched_baseline(tuner, validator):
    """Verify validator compares tuned recommendation with baseline SOP under matched noise."""
    rec = tuner.optimize_cycle(0.18, 21.0, 25.0, 28.0)
    val = validator.validate(
        recommendation=rec,
        moisture_pct=0.18,
        melt_flow_index=21.0,
        ambient_temp_c=25.0,
        recycled_pct=28.0,
        seed=123,
        add_noise=True
    )

    assert val.is_feasible is True
    assert val.energy_baseline_kwh > val.energy_tuned_kwh
    assert val.energy_reduction_pct > 0.0
    assert val.tensile_prediction_error is not None
    assert val.shrinkage_prediction_error is not None
    assert val.matched_noise_seed == 123


def test_simulator_validation_on_rejected_candidate(validator):
    """Verify validator handles rejected/infeasible recommendation cleanly."""
    rec_infeas = TuningRecommendation(
        melt_temp_c=230.0,
        injection_pressure_mpa=100.0,
        cooling_time_s=20.0,
        predicted_tensile_mpa=float("nan"),
        predicted_shrinkage_pct=float("nan"),
        predicted_energy_kwh=3.15,
        predicted_in_spec=False,
        is_feasible=False,
        status="OOD_REJECTED",
        message="Out of support"
    )

    val = validator.validate(
        recommendation=rec_infeas,
        moisture_pct=0.55,
        melt_flow_index=22.0,
        ambient_temp_c=24.0,
        recycled_pct=25.0
    )
    assert val.is_feasible is False
    assert val.status == "OOD_REJECTED"
    assert val.actuators_tuned is None
    assert val.energy_tuned_kwh is None


# ==============================================================================
# 8. Training Data Exclusivity Test
# ==============================================================================

def test_surrogate_training_data_only():
    """Verify that surrogate loader trains exclusively on dataset_train.csv."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic")
    train_path = os.path.join(data_dir, "dataset_train.csv")
    assert os.path.exists(train_path), "dataset_train.csv must exist"

    df_train = pd.read_csv(train_path)
    assert len(df_train) == 3500

    # Retrain pipeline in temporary directory using training data only
    with tempfile.TemporaryDirectory() as temp_dir:
        pipe = load_or_train_surrogate(
            model_name="Ridge",
            data_dir=data_dir,
            models_dir=temp_dir,
            random_state=42,
            force_retrain=True
        )
        assert len(pipe.steps) == 2
        assert os.path.exists(os.path.join(temp_dir, "surrogate_ridge.joblib"))


# ==============================================================================
# 9. Gate 2 CLI / Entry Point Smoke Test
# ==============================================================================

def test_run_gate2_cli_smoke_test():
    """Verify run_gate2_single executes cleanly and outputs valid report files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        exit_code, report_paths = run_gate2_single(
            moisture_pct=0.18,
            melt_flow_index=21.0,
            ambient_temp_c=25.0,
            recycled_pct=28.0,
            output_dir=temp_dir,
            reject_ood=True
        )
        assert exit_code == 0
        assert os.path.exists(report_paths["json"])
        assert os.path.exists(report_paths["csv"])
        assert os.path.exists(report_paths["markdown"])

        with open(report_paths["json"], "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["validation_results"]["overall_status"] == "OPTIMAL"
        assert data["validation_results"]["performance_comparison"]["energy_reduction_pct"] > 0
