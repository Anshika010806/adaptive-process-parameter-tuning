"""
Unit Test Suite for Physical Process Simulator and Synthetic Data Generation.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
"""

import math
import os
import sys

# Ensure repository root is in sys.path when script is executed directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import pytest
from src.simulation.process_simulator import PolymerInjectionSimulator, SimulationResult
from src.simulation.data_generator import DataGenerator


@pytest.fixture
def sim():
    """Fixture providing initialized process simulator."""
    return PolymerInjectionSimulator()


@pytest.fixture
def nominal_inputs():
    """Nominal material disturbances and nominal SOP machine settings."""
    return {
        "moisture_pct": 0.15,
        "melt_flow_index": 22.0,
        "ambient_temp_c": 24.0,
        "recycled_pct": 25.0,
        "melt_temp_c": 230.0,
        "injection_pressure_mpa": 100.0,
        "cooling_time_s": 20.0
    }


# ============================================================================
# 1. Initialization and Configuration Tests
# ============================================================================

def test_simulator_initialization(sim):
    """Verify simulator loads non-trivial physical parameters properly."""
    assert sim.S_base > 40.0
    assert sim.T_ref == 230.0
    assert sim.P_ref == 100.0
    assert sim.t_ref == 20.0
    assert sim.spec_S_min == 49.0
    assert sim.spec_S_max == 55.0
    assert sim.spec_V_min == 0.80
    assert sim.spec_V_max == 1.60


# ============================================================================
# 2. Deterministic Reproducibility Tests
# ============================================================================

def test_deterministic_reproducibility(sim, nominal_inputs):
    """Ensure identical random seeds yield byte-for-byte identical outcomes."""
    rng1 = np.random.default_rng(42)
    rng2 = np.random.default_rng(42)

    res1 = sim.evaluate_single(**nominal_inputs, add_noise=True, rng=rng1)
    res2 = sim.evaluate_single(**nominal_inputs, add_noise=True, rng=rng2)

    assert math.isclose(res1.tensile_strength_mpa, res2.tensile_strength_mpa, rel_tol=1e-12)
    assert math.isclose(res1.volumetric_shrinkage_pct, res2.volumetric_shrinkage_pct, rel_tol=1e-12)
    assert res1.in_spec_flag == res2.in_spec_flag


def test_stochastic_variation_with_different_seeds(sim, nominal_inputs):
    """Ensure distinct random seeds generate realistic stochastic variations."""
    rng1 = np.random.default_rng(42)
    rng2 = np.random.default_rng(999)

    res1 = sim.evaluate_single(**nominal_inputs, add_noise=True, rng=rng1)
    res2 = sim.evaluate_single(**nominal_inputs, add_noise=True, rng=rng2)

    assert not math.isclose(res1.tensile_strength_mpa, res2.tensile_strength_mpa, rel_tol=1e-7)


def test_noiseless_evaluation_is_strictly_deterministic(sim, nominal_inputs):
    """Noiseless evaluations must be identical without requiring RNG."""
    res1 = sim.evaluate_single(**nominal_inputs, add_noise=False)
    res2 = sim.evaluate_single(**nominal_inputs, add_noise=False)

    assert res1.tensile_strength_mpa == res2.tensile_strength_mpa
    assert res1.volumetric_shrinkage_pct == res2.volumetric_shrinkage_pct
    assert res1.energy_kwh == res2.energy_kwh


# ============================================================================
# 3. Physical Response Curves and Nonlinear Interactions
# ============================================================================

def test_nominal_operating_point_in_spec(sim, nominal_inputs):
    """Under nominal conditions, without noise, the part must be squarely in-spec."""
    res = sim.evaluate_single(**nominal_inputs, add_noise=False)
    assert sim.spec_S_min <= res.tensile_strength_mpa <= sim.spec_S_max
    assert sim.spec_V_min <= res.volumetric_shrinkage_pct <= sim.spec_V_max
    assert res.in_spec_flag == 1
    assert res.tensile_in_spec == 1
    assert res.shrinkage_in_spec == 1
    assert res.target_infeasible_flag == 0


def test_temperature_parabolic_degradation(sim, nominal_inputs):
    """
    Thermal response must be concave (parabolic):
    Both under-heating (210 C) and severe over-heating (255 C) degrade tensile strength
    compared to the optimal window near 230 C.
    """
    params_opt = nominal_inputs.copy()
    params_opt["melt_temp_c"] = 230.0

    params_cold = nominal_inputs.copy()
    params_cold["melt_temp_c"] = 208.0

    params_hot = nominal_inputs.copy()
    params_hot["melt_temp_c"] = 254.0

    res_opt = sim.evaluate_single(**params_opt, add_noise=False)
    res_cold = sim.evaluate_single(**params_cold, add_noise=False)
    res_hot = sim.evaluate_single(**params_hot, add_noise=False)

    assert res_opt.tensile_strength_mpa > res_cold.tensile_strength_mpa
    assert res_opt.tensile_strength_mpa > res_hot.tensile_strength_mpa


def test_pressure_monotonicity(sim, nominal_inputs):
    """
    Increasing injection packing pressure:
    1. Monotonically increases tensile strength (denser packing, micro-void collapse).
    2. Monotonically decreases volumetric shrinkage (compensates thermal contraction).
    """
    params_low_p = nominal_inputs.copy()
    params_low_p["injection_pressure_mpa"] = 70.0

    params_high_p = nominal_inputs.copy()
    params_high_p["injection_pressure_mpa"] = 140.0

    res_low = sim.evaluate_single(**params_low_p, add_noise=False)
    res_high = sim.evaluate_single(**params_high_p, add_noise=False)

    assert res_high.tensile_strength_mpa > res_low.tensile_strength_mpa
    assert res_high.volumetric_shrinkage_pct < res_low.volumetric_shrinkage_pct


def test_moisture_penalty_defect_generation(sim, nominal_inputs):
    """
    Elevated moisture content (e.g. 0.45% in wet recycled batches)
    significantly degrades tensile strength, driving parts out of specification under static SOP.
    """
    params_dry = nominal_inputs.copy()
    params_dry["moisture_pct"] = 0.10

    params_wet = nominal_inputs.copy()
    params_wet["moisture_pct"] = 0.45

    res_dry = sim.evaluate_single(**params_dry, add_noise=False)
    res_wet = sim.evaluate_single(**params_wet, add_noise=False)

    assert res_dry.tensile_strength_mpa > res_wet.tensile_strength_mpa
    # Wet batch under static SOP drops below minimum spec (49.0 MPa)
    assert res_wet.tensile_strength_mpa < sim.spec_S_min
    assert res_wet.tensile_in_spec == 0
    assert res_wet.in_spec_flag == 0


def test_cooling_transient_stabilization(sim, nominal_inputs):
    """
    Short cooling times (<20s) cause incomplete crystallization and high post-ejection shrinkage.
    Longer cooling times stabilize dimensions.
    """
    params_short = nominal_inputs.copy()
    params_short["cooling_time_s"] = 13.0

    params_long = nominal_inputs.copy()
    params_long["cooling_time_s"] = 30.0

    res_short = sim.evaluate_single(**params_short, add_noise=False)
    res_long = sim.evaluate_single(**params_long, add_noise=False)

    assert res_short.volumetric_shrinkage_pct > res_long.volumetric_shrinkage_pct
    assert res_short.tensile_strength_mpa < res_long.tensile_strength_mpa


def test_energy_cost_monotonicity(sim, nominal_inputs):
    """Specific energy consumption must increase with higher melt temp, higher pressure, and longer dwell."""
    base_res = sim.evaluate_single(**nominal_inputs, add_noise=False)

    params_hot = nominal_inputs.copy()
    params_hot["melt_temp_c"] = 250.0
    assert sim.evaluate_single(**params_hot, add_noise=False).energy_kwh > base_res.energy_kwh

    params_press = nominal_inputs.copy()
    params_press["injection_pressure_mpa"] = 130.0
    assert sim.evaluate_single(**params_press, add_noise=False).energy_kwh > base_res.energy_kwh

    params_dwell = nominal_inputs.copy()
    params_dwell["cooling_time_s"] = 28.0
    assert sim.evaluate_single(**params_dwell, add_noise=False).energy_kwh > base_res.energy_kwh


# ============================================================================
# 4. Input Validation and Guardrail Tests
# ============================================================================

def test_input_validation_catches_negative_moisture(sim, nominal_inputs):
    """Moisture cannot be negative."""
    bad_inputs = nominal_inputs.copy()
    bad_inputs["moisture_pct"] = -0.05
    with pytest.raises(ValueError, match="Moisture content cannot be negative"):
        sim.evaluate_single(**bad_inputs)


def test_input_validation_catches_nan_and_inf(sim, nominal_inputs):
    """NaN or Inf inputs must raise ValueError."""
    bad_inputs = nominal_inputs.copy()
    bad_inputs["melt_flow_index"] = float("nan")
    with pytest.raises(ValueError, match="Input contains NaN or Inf"):
        sim.evaluate_single(**bad_inputs)

    bad_inputs["melt_flow_index"] = float("inf")
    with pytest.raises(ValueError, match="Input contains NaN or Inf"):
        sim.evaluate_single(**bad_inputs)


def test_input_validation_catches_unphysical_temperatures(sim, nominal_inputs):
    """Melt temperature outside [100, 350] C must raise ValueError."""
    bad_inputs = nominal_inputs.copy()
    bad_inputs["melt_temp_c"] = 50.0
    with pytest.raises(ValueError, match="Melt temperature unphysical"):
        sim.evaluate_single(**bad_inputs)


# ============================================================================
# 5. Vectorized Batch Consistency Tests
# ============================================================================

def test_batch_vs_single_evaluation_exact_consistency(sim, nominal_inputs):
    """Vectorized evaluate_batch must match iterative evaluate_single numerically."""
    rows = []
    # Create 10 varied cycles
    for i in range(10):
        row = nominal_inputs.copy()
        row["moisture_pct"] += i * 0.02
        row["melt_flow_index"] -= i * 0.5
        row["melt_temp_c"] += (i - 5) * 2.0
        row["injection_pressure_mpa"] += (i - 5) * 4.0
        rows.append(row)

    df_in = pd.DataFrame(rows)
    df_batch = sim.evaluate_batch(df_in, add_noise=False)

    for i in range(10):
        single_res = sim.evaluate_single(**rows[i], add_noise=False)
        assert math.isclose(
            df_batch.iloc[i]["tensile_strength_mpa"],
            single_res.tensile_strength_mpa,
            rel_tol=1e-12
        )
        assert math.isclose(
            df_batch.iloc[i]["volumetric_shrinkage_pct"],
            single_res.volumetric_shrinkage_pct,
            rel_tol=1e-12
        )
        assert math.isclose(
            df_batch.iloc[i]["energy_kwh"],
            single_res.energy_kwh,
            rel_tol=1e-12
        )
        assert df_batch.iloc[i]["in_spec_flag"] == single_res.in_spec_flag


# ============================================================================
# 6. Data Generator Tests
# ============================================================================

def test_data_generator_in_distribution_shapes(sim):
    """Ensure DataGenerator constructs valid schema and expected row count."""
    generator = DataGenerator(simulator=sim)
    df = generator.generate_in_distribution_dataset(n=100, seed=42, explore_controls=True)

    expected_cols = [
        "cycle_id", "moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct",
        "melt_temp_c", "injection_pressure_mpa", "cooling_time_s",
        "tensile_strength_mpa", "volumetric_shrinkage_pct", "energy_kwh",
        "in_spec_flag", "tensile_in_spec", "shrinkage_in_spec", "target_infeasible_flag"
    ]
    assert len(df) == 100
    for col in expected_cols:
        assert col in df.columns
    assert not df.isnull().any().any()


def test_data_generator_ood_scenarios_execute(sim):
    """Ensure all 4 OOD stress dataset generation routines execute with valid outputs."""
    generator = DataGenerator(simulator=sim)

    df_ood1 = generator.generate_ood_1_feedstock_shift(n=50, seed=301)
    assert len(df_ood1) == 50
    assert df_ood1["moisture_pct"].mean() > 0.35  # Degraded moisture shift verified

    df_ood2 = generator.generate_ood_2_thermal_shift(n=50, seed=302)
    assert len(df_ood2) == 50
    assert df_ood2["ambient_temp_c"].mean() > 33.0  # Heatwave shift verified

    df_ood3 = generator.generate_ood_3_extrapolation(n=50, seed=303)
    assert len(df_ood3) == 50
    assert (df_ood3["moisture_pct"] > 0.50).all()  # Strict extrapolation support verified

    df_ood4 = generator.generate_ood_4_sensor_noise(n=50, seed=304)
    assert len(df_ood4) == 50


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", __file__]))

