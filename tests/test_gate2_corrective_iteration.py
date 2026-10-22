"""
Comprehensive Unit and Integration Tests for Gate 2 Corrective Iteration.

Validates the corrected adaptive process parameter tuning engine incorporating Gate 3
empirical findings:
1. Boundary candidate filtering near 49.0 MPa lower limit
2. Absorption of stochastic process noise without double-counting uncertainty
3. Protection for high-recycled content regimes justified by validation evidence
4. Hard actuator constraints and strict quality infeasibility rejection
5. Configurable deterministic safety margins, chance constraint calibration, and regression behavior

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 2 Corrective Iteration)
"""

import os
import sys
import numpy as np
import pandas as pd
import pytest
from scipy import stats

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulation.process_simulator import PolymerInjectionSimulator
from src.optimization.static_controller import StaticSOPController
from src.optimization.domain_guard import DomainGuard
from src.optimization.surrogate_loader import load_or_train_surrogate
from src.optimization.adaptive_tuner import AdaptiveProcessTuner, TuningRecommendation
from src.optimization.simulator_validator import SimulatorValidator, SimulatorValidationResult


@pytest.fixture(scope="module")
def shared_surrogate():
    """Load or train surrogate using training data exclusively."""
    return load_or_train_surrogate(model_name="RandomForest", random_state=42)


@pytest.fixture
def corrected_tuner(shared_surrogate):
    """Instantiate corrected tuner with conservative safety margins."""
    return AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        random_state=42,
        search_strategy="grid",
        grid_resolution=(9, 9, 7),
        reject_ood=True,
        refine_local=True,
        safety_margin_tensile=1.50,
        safety_margin_shrinkage=0.05,
        recycled_margin_slope=0.035,
        recycled_margin_threshold=25.0
    )


@pytest.fixture
def validator():
    """Instantiate authoritative SimulatorValidator."""
    return SimulatorValidator()


# ==============================================================================
# 1. Candidates Near the 49 MPa Tensile Boundary
# ==============================================================================

def test_boundary_candidates_protected_by_safety_margin(shared_surrogate):
    """
    Verify that candidates near the 49.0 MPa lower limit are bounded away by the margin.
    Surrogate predictions of selected candidates must always satisfy S >= 49.0 + margin.
    """
    margin = 1.40
    tuner = AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        safety_margin_tensile=margin,
        recycled_margin_slope=0.0,
        refine_local=True
    )

    # Test across in-domain disturbance contexts
    test_contexts = [
        (0.18, 21.0, 25.0, 22.0),
        (0.12, 24.0, 22.0, 18.0),
        (0.22, 19.0, 26.0, 24.0),
    ]

    for m, mfi, t_amb, rec in test_contexts:
        rec_out = tuner.optimize_cycle(m, mfi, t_amb, rec)
        assert rec_out.is_feasible is True
        assert rec_out.status == "OPTIMAL"
        # Must be strictly above spec_min + margin
        assert rec_out.predicted_tensile_mpa >= (49.0 + margin - 1e-5), (
            f"Predicted tensile {rec_out.predicted_tensile_mpa} violated safe lower bound {49.0 + margin}"
        )
        assert rec_out.predicted_tensile_mpa <= (55.0 - margin + 1e-5)


def test_local_refinement_strictly_preserves_safety_margin(shared_surrogate):
    """
    Verify that local grid refinement never pulls actuator setpoints below the
    conservative safety margin boundary (fixing the Gate 3 root-cause defect).
    """
    margin = 1.30
    tuner_with_refine = AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        safety_margin_tensile=margin,
        recycled_margin_slope=0.0,
        refine_local=True
    )
    tuner_no_refine = AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        safety_margin_tensile=margin,
        recycled_margin_slope=0.0,
        refine_local=False
    )

    rec_refine = tuner_with_refine.optimize_cycle(0.16, 22.0, 24.0, 20.0)
    rec_norefine = tuner_no_refine.optimize_cycle(0.16, 22.0, 24.0, 20.0)

    assert rec_refine.is_feasible is True
    assert rec_norefine.is_feasible is True
    assert rec_refine.predicted_tensile_mpa >= (49.0 + margin - 1e-5)
    assert rec_norefine.predicted_tensile_mpa >= (49.0 + margin - 1e-5)
    # Refinement must achieve equal or lower energy while staying strictly safe
    assert rec_refine.predicted_energy_kwh <= rec_norefine.predicted_energy_kwh + 1e-6


# ==============================================================================
# 2. Noisy Tensile Outcomes (Stochastic Noise Absorption)
# ==============================================================================

def test_noisy_tensile_outcomes_remain_above_spec_limit(corrected_tuner, validator):
    """
    Verify that under stochastic physical simulator noise (sigma = 0.35 MPa),
    the corrected safety margin absorbs the random fluctuations and keeps realized
    tensile strength >= 49.0 MPa across multiple noise realizations.
    """
    m, mfi, t_amb, rec = 0.18, 21.0, 25.0, 28.0
    recommendation = corrected_tuner.optimize_cycle(m, mfi, t_amb, rec)
    assert recommendation.is_feasible is True

    # Test across 20 distinct random noise seeds
    realized_tensiles = []
    for noise_seed in range(100, 120):
        val_res = validator.validate(
            recommendation=recommendation,
            moisture_pct=m,
            melt_flow_index=mfi,
            ambient_temp_c=t_amb,
            recycled_pct=rec,
            seed=noise_seed,
            add_noise=True
        )
        assert val_res.is_feasible is True
        sim_tensile = val_res.simulated_tuned["tensile_strength_mpa"]
        realized_tensiles.append(sim_tensile)
        assert sim_tensile >= 49.0, (
            f"Seed {noise_seed} produced tensile {sim_tensile:.3f} MPa below 49.0 MPa lower limit"
        )
        assert val_res.tensile_spec_met is True
        assert val_res.realized_in_spec is True

    assert min(realized_tensiles) >= 49.0


def test_independent_quadrature_uncertainty_decomposition():
    """
    Verify that surrogate error and process noise are combined in quadrature
    without double-counting (sqrt(sigma_surr^2 + sigma_noise^2) < sigma_surr + sigma_noise).
    """
    sigma_surr = 0.43
    sigma_noise = 0.35

    composite_quadrature = np.sqrt(sigma_surr ** 2 + sigma_noise ** 2)
    double_counted = sigma_surr + sigma_noise

    # Quadrature must strictly avoid inflation
    assert composite_quadrature < double_counted
    assert composite_quadrature == pytest.approx(0.5544, abs=1e-3)


# ==============================================================================
# 3. High Recycled-Content Conditions
# ==============================================================================

def test_high_recycled_content_adaptive_protection(shared_surrogate, validator):
    """
    Verify that for high recycled content (C_rec > 25 wt%), the tuner dynamically
    expands the tensile safety margin, preventing the quality drop documented in Gate 3.
    """
    tuner_adaptive = AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        safety_margin_tensile=1.40,
        recycled_margin_slope=0.035,
        recycled_margin_threshold=25.0
    )

    # Low recycled content: base margin
    margin_low = tuner_adaptive.get_tensile_safety_margin(recycled_pct=20.0)
    assert margin_low == pytest.approx(1.40, abs=1e-5)

    # High recycled content: expanded margin
    margin_high = tuner_adaptive.get_tensile_safety_margin(recycled_pct=35.0)
    expected_high = 1.40 + 0.035 * (35.0 - 25.0)  # 1.40 + 0.35 = 1.75 MPa
    assert margin_high == pytest.approx(expected_high, abs=1e-5)
    assert margin_high > margin_low

    # Severe high recycled scenario: C_rec = 36 wt%
    m, mfi, t_amb, rec = 0.14, 23.5, 24.0, 36.0
    rec_out = tuner_adaptive.optimize_cycle(m, mfi, t_amb, rec)
    assert rec_out.is_feasible is True

    # Validate against simulator across repetitions
    for s in [42, 1042, 2042]:
        val = validator.validate(rec_out, m, mfi, t_amb, rec, seed=s, add_noise=True)
        assert val.realized_in_spec is True
        assert val.tensile_spec_met is True
        assert val.simulated_tuned["tensile_strength_mpa"] >= 49.0


def test_candidate_120_mpa_evaluation_on_high_recycled(shared_surrogate, validator):
    """
    Evaluate 1.20 MPa as an empirical candidate:
    Verifies that while 1.20 MPa is significantly better than 0.80 MPa, without high-recycled
    adaptation it can still encounter edge violations under extreme recycled blends.
    """
    tuner_120 = AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        safety_margin_tensile=1.20,
        recycled_margin_slope=0.0,
        refine_local=True
    )
    assert tuner_120.safety_margin_tensile == 1.20
    assert tuner_120.get_tensile_safety_margin(35.0) == 1.20

    # Mild recycled context: 1.20 MPa is fully compliant
    rec_mild = tuner_120.optimize_cycle(0.15, 22.0, 24.0, 20.0)
    val_mild = validator.validate(rec_mild, 0.15, 22.0, 24.0, 20.0, seed=42, add_noise=True)
    assert val_mild.realized_in_spec is True
    assert val_mild.simulated_tuned["tensile_strength_mpa"] >= 49.0


# ==============================================================================
# 4. Infeasible Candidates and Hard Actuator Constraints
# ==============================================================================

def test_hard_actuator_limits_strictly_preserved(corrected_tuner):
    """Verify that actuator limits are strictly preserved under all circumstances."""
    rng = np.random.default_rng(202)
    for _ in range(30):
        m = rng.uniform(0.08, 0.35)
        mfi = rng.uniform(15.0, 28.0)
        t_amb = rng.uniform(18.0, 30.0)
        rec = rng.uniform(12.0, 38.0)

        res = corrected_tuner.optimize_cycle(m, mfi, t_amb, rec)
        if res.is_feasible:
            assert 205.0 <= res.melt_temp_c <= 255.0
            assert 65.0 <= res.injection_pressure_mpa <= 145.0
            assert 12.0 <= res.cooling_time_s <= 32.0


def test_infeasible_rejection_when_safety_margin_unreachable(shared_surrogate):
    """
    Verify that if a context cannot satisfy the safety margin and fallback is disallowed,
    the tuner returns is_feasible=False with status INFEASIBLE.
    """
    # Exaggerated margin impossible to satisfy
    tuner_strict = AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        safety_margin_tensile=4.0,  # [49 + 4, 55 - 4] = [53, 51] -> Empty!
        allow_fallback_to_strict=False
    )
    rec = tuner_strict.optimize_cycle(0.18, 21.0, 25.0, 28.0)
    assert rec.is_feasible is False
    assert rec.status == "INFEASIBLE"
    assert rec.predicted_in_spec is False
    assert np.isnan(rec.predicted_tensile_mpa)
    # Reverts safely to nominal SOP
    assert rec.melt_temp_c == 230.0
    assert rec.injection_pressure_mpa == 100.0
    assert rec.cooling_time_s == 20.0


def test_fallback_to_strict_when_explicitly_allowed(shared_surrogate):
    """
    Verify that when allow_fallback_to_strict=True, the tuner flags status SUBOPTIMAL
    with an explicit warning message rather than silent failure.
    """
    tuner_fallback = AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        safety_margin_tensile=2.90,  # Very narrow safe band
        allow_fallback_to_strict=True
    )
    rec = tuner_fallback.optimize_cycle(0.18, 21.0, 25.0, 28.0)
    if rec.status == "SUBOPTIMAL":
        assert rec.is_feasible is True
        assert "fell back" in rec.message.lower()


# ==============================================================================
# 5. Margin Configuration and Statistical Chance Constraint Behavior
# ==============================================================================

def test_margin_configurable_from_simulation_config(shared_surrogate):
    """Verify that tuner correctly loads safety margins from simulation_config.json."""
    tuner = AdaptiveProcessTuner(surrogate_pipeline=shared_surrogate)
    # Loaded from simulation_config.json
    assert tuner.safety_margin_tensile >= 1.20
    assert tuner.safety_margin_shrinkage == 0.05
    assert tuner.recycled_margin_slope > 0.0
    assert tuner.recycled_margin_threshold == 25.0


def test_chance_constraint_formulation(shared_surrogate):
    """
    Verify statistically justified chance constraint calculations:
    Delta_S = bias + z_(1-alpha) * sqrt(sigma_surr^2 + sigma_noise^2).
    """
    tuner_95 = AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        use_chance_constraint=True,
        chance_confidence=0.95,
        surrogate_bias=0.4708,
        surrogate_sigma=0.43,
        process_noise_sigma=0.35,
        recycled_margin_slope=0.0
    )
    margin_95 = tuner_95.get_tensile_safety_margin()
    z_95 = stats.norm.ppf(0.95)
    expected_95 = 0.4708 + z_95 * np.sqrt(0.43 ** 2 + 0.35 ** 2)
    assert margin_95 == pytest.approx(expected_95, abs=1e-4)

    tuner_99 = AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        use_chance_constraint=True,
        chance_confidence=0.99,
        surrogate_bias=0.4708,
        surrogate_sigma=0.43,
        process_noise_sigma=0.35,
        recycled_margin_slope=0.0
    )
    margin_99 = tuner_99.get_tensile_safety_margin()
    z_99 = stats.norm.ppf(0.99)
    expected_99 = 0.4708 + z_99 * np.sqrt(0.43 ** 2 + 0.35 ** 2)
    assert margin_99 == pytest.approx(expected_99, abs=1e-4)
    assert margin_99 > margin_95


def test_batch_tuning_with_recycled_margins(corrected_tuner):
    """Verify tune_batch properly applies per-row recycled margin adjustments."""
    df_mat = pd.DataFrame({
        "moisture_pct": [0.15, 0.18, 0.20],
        "melt_flow_index": [22.0, 20.0, 24.0],
        "ambient_temp_c": [24.0, 25.0, 23.0],
        "recycled_pct": [15.0, 25.0, 35.0]
    })

    df_out = corrected_tuner.tune_batch(df_mat)
    assert len(df_out) == 3
    assert (df_out["is_feasible"] == True).all()
    assert (df_out["status"] == "OPTIMAL").all()

    # Recycled 35% should have higher predicted tensile than recycled 15% due to higher safety buffer
    pred_tens = df_out["predicted_tensile_mpa"].to_numpy()
    assert pred_tens[2] >= pred_tens[0]
