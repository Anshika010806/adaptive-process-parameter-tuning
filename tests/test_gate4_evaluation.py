"""
Comprehensive Unit and Integration Tests for Gate 4: Robustness, Sensitivity, and Ablation Evaluation.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 4 - Robustness and Ablation Evaluation)
"""

import os
import sys
import json
import tempfile
import numpy as np
import pandas as pd
import pytest

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulation.process_simulator import PolymerInjectionSimulator
from src.optimization.domain_guard import DomainGuard
from src.optimization.surrogate_loader import load_or_train_surrogate
from src.optimization.adaptive_tuner import AdaptiveProcessTuner
from src.validation.gate4_evaluator import (
    Gate4Evaluator,
    AblationVariantConfig,
    Gate4SummaryResult,
)
from src.validation.run_gate4 import run_gate4_evaluation


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def shared_surrogate():
    """Load or train surrogate once per test-session module."""
    return load_or_train_surrogate(model_name="RandomForest", random_state=42)


@pytest.fixture(scope="module")
def gate4_evaluator(shared_surrogate):
    """Instantiate a Gate4Evaluator with shared surrogate for the module."""
    return Gate4Evaluator(surrogate_pipeline=shared_surrogate, random_state=42)


@pytest.fixture(scope="module")
def small_contexts(gate4_evaluator):
    """5-context sample for fast test execution."""
    return gate4_evaluator.sample_supported_contexts(n=5, seed=42)


# ==============================================================================
# 1. Context Sampling & Domain Guard Tests
# ==============================================================================

def test_sample_supported_contexts_within_bounds(gate4_evaluator):
    """All sampled operating contexts must be within documented training support."""
    df = gate4_evaluator.sample_supported_contexts(n=20, seed=77)
    assert len(df) == 20

    guard = DomainGuard()
    for _, row in df.iterrows():
        res = guard.validate_material(
            moisture_pct=row["moisture_pct"],
            melt_flow_index=row["melt_flow_index"],
            ambient_temp_c=row["ambient_temp_c"],
            recycled_pct=row["recycled_pct"],
        )
        assert res.is_valid is True, f"Context out-of-bounds: {dict(row)}"
        assert res.is_in_support is True
        assert res.status == "VALID"


def test_sample_supported_contexts_reproducible(gate4_evaluator):
    """Identical seeds must produce identical context DataFrames."""
    df1 = gate4_evaluator.sample_supported_contexts(n=10, seed=100)
    df2 = gate4_evaluator.sample_supported_contexts(n=10, seed=100)
    pd.testing.assert_frame_equal(df1, df2)


def test_sample_supported_contexts_column_set(gate4_evaluator):
    """Sampled DataFrame must contain all required material columns."""
    df = gate4_evaluator.sample_supported_contexts(n=5, seed=1)
    required_cols = {"moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct", "context_id"}
    assert required_cols.issubset(set(df.columns))


# ==============================================================================
# 2. AblationVariantConfig Tests
# ==============================================================================

def test_ablation_variant_config_is_frozen():
    """AblationVariantConfig instances must be immutable (frozen dataclass)."""
    var = AblationVariantConfig(
        variant_id="test_var",
        display_name="Test Variant",
        description="A test variant",
        safety_margin_tensile=1.50,
        safety_margin_shrinkage=0.05,
        recycled_margin_slope=0.035,
        recycled_margin_threshold=25.0,
    )
    with pytest.raises((AttributeError, TypeError)):
        var.safety_margin_tensile = 0.0  # type: ignore[misc]


def test_create_tuner_returns_none_for_static_sop(gate4_evaluator):
    """Static SOP variant must return None from create_tuner (no adaptive tuner instantiated)."""
    sop_var = AblationVariantConfig(
        variant_id="static_sop",
        display_name="Static SOP",
        description="SOP reference",
        safety_margin_tensile=0.0,
        safety_margin_shrinkage=0.0,
        recycled_margin_slope=0.0,
        recycled_margin_threshold=25.0,
        is_static_sop=True,
    )
    tuner = gate4_evaluator.create_tuner(sop_var)
    assert tuner is None


def test_create_tuner_returns_adaptive_tuner_for_non_static(gate4_evaluator):
    """Non-SOP variants must produce a properly-configured AdaptiveProcessTuner."""
    var = AblationVariantConfig(
        variant_id="full_corrected",
        display_name="Full Corrected",
        description="",
        safety_margin_tensile=1.50,
        safety_margin_shrinkage=0.05,
        recycled_margin_slope=0.035,
        recycled_margin_threshold=25.0,
    )
    tuner = gate4_evaluator.create_tuner(var)
    assert isinstance(tuner, AdaptiveProcessTuner)
    assert tuner.safety_margin_tensile == pytest.approx(1.50)
    assert tuner.recycled_margin_slope == pytest.approx(0.035)


# ==============================================================================
# 3. Single-Cycle Evaluation Tests
# ==============================================================================

def test_evaluate_tuner_on_context_returns_required_keys(gate4_evaluator, small_contexts):
    """Single-cycle evaluation dict must contain all required result keys."""
    var = AblationVariantConfig(
        variant_id="full_corrected",
        display_name="Full Corrected",
        description="",
        safety_margin_tensile=1.50,
        safety_margin_shrinkage=0.05,
        recycled_margin_slope=0.035,
        recycled_margin_threshold=25.0,
    )
    tuner = gate4_evaluator.create_tuner(var)
    row = small_contexts.iloc[0]

    result = gate4_evaluator.evaluate_tuner_on_context(
        tuner=tuner,
        m=float(row["moisture_pct"]),
        mfi=float(row["melt_flow_index"]),
        t_amb=float(row["ambient_temp_c"]),
        rec_pct=float(row["recycled_pct"]),
        matched_seed=42,
        add_noise=True,
    )

    required_keys = {
        "tuner_status", "tuner_feasible", "optimization_latency_ms",
        "deployed_melt_temp_c", "deployed_injection_pressure_mpa", "deployed_cooling_time_s",
        "actuator_limits_respected",
        "sim_tensile_mpa", "sim_shrinkage_pct", "sim_energy_kwh",
        "sim_tensile_in_spec", "sim_shrinkage_in_spec", "sim_all_in_spec",
        "energy_reduction_kwh", "energy_reduction_pct",
        "quality_violation", "false_positive_quality",
    }
    assert required_keys.issubset(set(result.keys()))


def test_evaluate_tuner_on_context_actuator_bounds(gate4_evaluator, small_contexts):
    """Deployed actuator setpoints must always be within hard machine limits."""
    var = AblationVariantConfig(
        variant_id="full_corrected",
        display_name="Full Corrected",
        description="",
        safety_margin_tensile=1.50,
        safety_margin_shrinkage=0.05,
        recycled_margin_slope=0.035,
        recycled_margin_threshold=25.0,
    )
    tuner = gate4_evaluator.create_tuner(var)

    for idx in range(len(small_contexts)):
        row = small_contexts.iloc[idx]
        result = gate4_evaluator.evaluate_tuner_on_context(
            tuner=tuner,
            m=float(row["moisture_pct"]),
            mfi=float(row["melt_flow_index"]),
            t_amb=float(row["ambient_temp_c"]),
            rec_pct=float(row["recycled_pct"]),
            matched_seed=42 + idx,
            add_noise=False,
        )
        assert result["actuator_limits_respected"] is True, (
            f"Actuator violation at context {idx}: melt={result['deployed_melt_temp_c']:.1f}, "
            f"pressure={result['deployed_injection_pressure_mpa']:.1f}, "
            f"cool={result['deployed_cooling_time_s']:.1f}"
        )
        assert 205.0 - 1e-3 <= result["deployed_melt_temp_c"] <= 255.0 + 1e-3
        assert 65.0 - 1e-3 <= result["deployed_injection_pressure_mpa"] <= 145.0 + 1e-3
        assert 12.0 - 1e-3 <= result["deployed_cooling_time_s"] <= 32.0 + 1e-3


def test_evaluate_static_sop_uses_fixed_setpoints(gate4_evaluator, small_contexts):
    """Static SOP baseline must always deploy T=230C, P=100 MPa, t=20 s."""
    row = small_contexts.iloc[0]
    result = gate4_evaluator.evaluate_tuner_on_context(
        tuner=None,
        m=float(row["moisture_pct"]),
        mfi=float(row["melt_flow_index"]),
        t_amb=float(row["ambient_temp_c"]),
        rec_pct=float(row["recycled_pct"]),
        matched_seed=None,
        add_noise=False,
    )
    assert result["tuner_status"] == "STATIC_SOP"
    assert result["deployed_melt_temp_c"] == pytest.approx(230.0)
    assert result["deployed_injection_pressure_mpa"] == pytest.approx(100.0)
    assert result["deployed_cooling_time_s"] == pytest.approx(20.0)


def test_energy_reduction_arithmetic_correctness(gate4_evaluator, small_contexts):
    """Energy reduction kWh and pct must match the difference of simulator runs (no-noise)."""
    var = AblationVariantConfig(
        variant_id="full_corrected",
        display_name="Full Corrected",
        description="",
        safety_margin_tensile=1.50,
        safety_margin_shrinkage=0.05,
        recycled_margin_slope=0.035,
        recycled_margin_threshold=25.0,
    )
    tuner = gate4_evaluator.create_tuner(var)
    row = small_contexts.iloc[1]

    result = gate4_evaluator.evaluate_tuner_on_context(
        tuner=tuner,
        m=float(row["moisture_pct"]),
        mfi=float(row["melt_flow_index"]),
        t_amb=float(row["ambient_temp_c"]),
        rec_pct=float(row["recycled_pct"]),
        matched_seed=None,
        add_noise=False,
    )

    expected_kwh = result["sim_baseline_energy_kwh"] - result["sim_energy_kwh"]
    expected_pct = (expected_kwh / result["sim_baseline_energy_kwh"]) * 100.0

    assert result["energy_reduction_kwh"] == pytest.approx(expected_kwh, abs=1e-6)
    assert result["energy_reduction_pct"] == pytest.approx(expected_pct, abs=1e-6)


def test_matched_noise_seed_determinism(gate4_evaluator, small_contexts):
    """Same matched seed must produce identical simulator outcomes across repeated calls."""
    var = AblationVariantConfig(
        variant_id="full_corrected",
        display_name="Full Corrected",
        description="",
        safety_margin_tensile=1.50,
        safety_margin_shrinkage=0.05,
        recycled_margin_slope=0.035,
        recycled_margin_threshold=25.0,
    )
    tuner = gate4_evaluator.create_tuner(var)
    row = small_contexts.iloc[0]

    # Clear cache to force fresh simulation
    gate4_evaluator._opt_cache.clear()
    r1 = gate4_evaluator.evaluate_tuner_on_context(
        tuner=tuner,
        m=float(row["moisture_pct"]),
        mfi=float(row["melt_flow_index"]),
        t_amb=float(row["ambient_temp_c"]),
        rec_pct=float(row["recycled_pct"]),
        matched_seed=99,
        add_noise=True,
    )

    gate4_evaluator._opt_cache.clear()
    r2 = gate4_evaluator.evaluate_tuner_on_context(
        tuner=tuner,
        m=float(row["moisture_pct"]),
        mfi=float(row["melt_flow_index"]),
        t_amb=float(row["ambient_temp_c"]),
        rec_pct=float(row["recycled_pct"]),
        matched_seed=99,
        add_noise=True,
    )

    assert r1["sim_tensile_mpa"] == pytest.approx(r2["sim_tensile_mpa"], abs=1e-7)
    assert r1["sim_shrinkage_pct"] == pytest.approx(r2["sim_shrinkage_pct"], abs=1e-7)
    assert r1["sim_energy_kwh"] == pytest.approx(r2["sim_energy_kwh"], abs=1e-7)


# ==============================================================================
# 4. Robustness Experiment Tests
# ==============================================================================

def test_robustness_experiment_output_structure(gate4_evaluator, small_contexts):
    """Robustness experiment must return a DataFrame and summary dict with expected keys."""
    df, summary = gate4_evaluator.run_robustness_experiment(
        contexts_df=small_contexts,
        repetitions=2,
        base_seed=42,
        alternate_seeds=[42, 1337],
        noise_levels=[0.0, 0.35],
    )

    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "noise_sigma" in df.columns
    assert "sim_tensile_mpa" in df.columns
    assert "quality_violation" in df.columns

    assert "noise_level_evaluations" in summary
    assert "seed_stability_evaluations" in summary
    assert "total_cycles" in summary

    # Check noise level keys
    assert "sigma_0.0" in summary["noise_level_evaluations"]
    assert "sigma_0.35" in summary["noise_level_evaluations"]


def test_robustness_noise_robustness_cycle_counts(gate4_evaluator, small_contexts):
    """Robustness experiment cycle counts must be N_contexts x N_reps per noise level."""
    n_contexts = len(small_contexts)
    repetitions = 2
    noise_levels = [0.0, 0.35]

    df, summary = gate4_evaluator.run_robustness_experiment(
        contexts_df=small_contexts,
        repetitions=repetitions,
        base_seed=42,
        alternate_seeds=[42],
        noise_levels=noise_levels,
    )

    for noise_sigma in noise_levels:
        expected_count = n_contexts * repetitions
        actual = summary["noise_level_evaluations"][f"sigma_{noise_sigma}"]["cycles_evaluated"]
        assert actual == expected_count, (
            f"Expected {expected_count} cycles at sigma={noise_sigma}, got {actual}"
        )


def test_robustness_actuator_bounds_always_respected(gate4_evaluator, small_contexts):
    """All deployed setpoints in robustness experiment must respect hard machine limits."""
    df, _ = gate4_evaluator.run_robustness_experiment(
        contexts_df=small_contexts,
        repetitions=2,
        base_seed=42,
        alternate_seeds=[42],
        noise_levels=[0.35],
    )

    assert df["actuator_limits_respected"].all(), "Actuator limit violation detected in robustness experiment!"


def test_robustness_noise_zero_means_no_stochastic_variation(gate4_evaluator, small_contexts):
    """With sigma=0 noise, repeated evaluations of same context must produce identical simulator outputs."""
    df, _ = gate4_evaluator.run_robustness_experiment(
        contexts_df=small_contexts.iloc[:2],
        repetitions=3,
        base_seed=42,
        alternate_seeds=[42],
        noise_levels=[0.0],
    )

    sub = df[df["noise_sigma"] == 0.0]
    # For each context, tensile values across repetitions should be identical
    for ctx_id in sub["context_id"].unique():
        ctx_sub = sub[sub["context_id"] == ctx_id]
        tensile_vals = ctx_sub["sim_tensile_mpa"].values
        assert np.allclose(tensile_vals, tensile_vals[0], atol=1e-6), (
            f"Non-zero variation at sigma=0 for context {ctx_id}: {tensile_vals}"
        )


# ==============================================================================
# 5. Sensitivity Experiment Tests
# ==============================================================================

def test_sensitivity_experiment_output_structure(gate4_evaluator, small_contexts):
    """Sensitivity experiment must return a DataFrame and summary with expected keys."""
    df, summary = gate4_evaluator.run_sensitivity_experiment(
        contexts_df=small_contexts,
        margin_levels=[0.0, 1.50],
        recycled_levels=[10.0, 25.0, 40.0],
        repetitions=2,
        base_seed=42,
    )

    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "sensitivity_type" in df.columns
    assert "sweep_param_value" in df.columns

    assert "tensile_margin_sweep" in summary
    assert "recycled_content_sweep" in summary
    assert "total_cycles" in summary


def test_sensitivity_recycled_levels_within_domain(gate4_evaluator):
    """Sensitivity recycled content sweep must stay strictly within [10.0, 40.0] wt%."""
    guard = DomainGuard()
    tested_levels = [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0]
    for rec_val in tested_levels:
        res = guard.validate_material(0.15, 22.0, 24.0, rec_val)
        assert res.is_in_support is True, f"recycled_pct={rec_val} is out of support!"


def test_sensitivity_margin_sweep_compliance_monotone_tendency(gate4_evaluator, small_contexts):
    """Higher tensile safety margins should generally not produce more defects than zero margin."""
    df, summary = gate4_evaluator.run_sensitivity_experiment(
        contexts_df=small_contexts,
        margin_levels=[0.0, 1.50],
        recycled_levels=[10.0, 40.0],
        repetitions=2,
        base_seed=42,
    )

    violations_zero = summary["tensile_margin_sweep"]["0.00_mpa"]["quality_violations"]
    violations_full = summary["tensile_margin_sweep"]["1.50_mpa"]["quality_violations"]

    # Full margin must have fewer or equal violations compared to zero margin
    assert violations_full <= violations_zero, (
        f"Full margin produced more defects ({violations_full}) than zero margin ({violations_zero})"
    )


# ==============================================================================
# 6. Ablation Experiment Tests
# ==============================================================================

def test_ablation_experiment_output_structure(gate4_evaluator, small_contexts):
    """Ablation experiment must return raw DataFrame, summary DataFrame, and dict."""
    df_raw, df_summary, ablation_dict = gate4_evaluator.run_ablation_experiment(
        contexts_df=small_contexts,
        repetitions=2,
        base_seed=42,
    )

    assert isinstance(df_raw, pd.DataFrame)
    assert isinstance(df_summary, pd.DataFrame)
    assert isinstance(ablation_dict, dict)

    assert "variant_id" in df_raw.columns
    assert "sim_all_in_spec" in df_raw.columns
    assert "energy_reduction_pct" in df_raw.columns
    assert "actuator_limits_respected" in df_raw.columns

    assert "variant_id" in df_summary.columns
    assert "overall_quality_compliance_pct" in df_summary.columns
    assert "total_defects" in df_summary.columns
    assert "actuator_limits_strictly_respected" in df_summary.columns

    assert "variants_evaluated" in ablation_dict
    assert "total_cycles" in ablation_dict


def test_ablation_expected_variant_ids_present(gate4_evaluator, small_contexts):
    """Ablation must include all 6 expected variant IDs."""
    _, df_summary, _ = gate4_evaluator.run_ablation_experiment(
        contexts_df=small_contexts,
        repetitions=2,
        base_seed=42,
    )

    expected_variants = {
        "full_corrected",
        "no_recycled_protection",
        "initial_baseline_margin",
        "candidate_margin_120",
        "unpadded_zero_margin",
        "static_sop",
    }
    actual_variants = set(df_summary["variant_id"].tolist())
    assert expected_variants == actual_variants, (
        f"Missing variants: {expected_variants - actual_variants}"
    )


def test_ablation_all_actuator_limits_respected(gate4_evaluator, small_contexts):
    """Actuator hard limits must be strictly respected across all ablation variants."""
    df_raw, df_summary, _ = gate4_evaluator.run_ablation_experiment(
        contexts_df=small_contexts,
        repetitions=2,
        base_seed=42,
    )

    # Check raw records
    violations = df_raw[~df_raw["actuator_limits_respected"]]
    assert len(violations) == 0, (
        f"Actuator violations found:\n"
        f"{violations[['variant_id', 'deployed_melt_temp_c', 'deployed_injection_pressure_mpa', 'deployed_cooling_time_s']].to_string()}"
    )

    # Check summary flags
    for _, row in df_summary.iterrows():
        assert row["actuator_limits_strictly_respected"] is True, (
            f"Variant '{row['variant_id']}' reported actuator limits violated"
        )


def test_ablation_matched_cycle_counts(gate4_evaluator, small_contexts):
    """Each ablation variant must be evaluated for exactly N_contexts x N_reps cycles."""
    n_contexts = len(small_contexts)
    repetitions = 2
    expected_cycles = n_contexts * repetitions

    _, df_summary, _ = gate4_evaluator.run_ablation_experiment(
        contexts_df=small_contexts,
        repetitions=repetitions,
        base_seed=42,
    )

    for _, row in df_summary.iterrows():
        assert row["total_cycles"] == expected_cycles, (
            f"Variant '{row['variant_id']}' has {row['total_cycles']} cycles, expected {expected_cycles}"
        )


def test_ablation_full_corrected_compliance_geq_no_recycled_protection(gate4_evaluator, small_contexts):
    """Full corrected tuner must achieve >= overall quality compliance vs no-recycled-protection variant."""
    _, df_summary, _ = gate4_evaluator.run_ablation_experiment(
        contexts_df=small_contexts,
        repetitions=3,
        base_seed=42,
    )

    full_row = df_summary[df_summary["variant_id"] == "full_corrected"].iloc[0]
    no_rec_row = df_summary[df_summary["variant_id"] == "no_recycled_protection"].iloc[0]

    assert full_row["overall_quality_compliance_pct"] >= no_rec_row["overall_quality_compliance_pct"], (
        f"Full corrected ({full_row['overall_quality_compliance_pct']:.2f}%) should be >= "
        f"no recycled protection ({no_rec_row['overall_quality_compliance_pct']:.2f}%)"
    )


def test_ablation_full_corrected_compliance_geq_unpadded(gate4_evaluator, small_contexts):
    """Full corrected tuner must achieve >= overall quality compliance vs zero-margin variant."""
    _, df_summary, _ = gate4_evaluator.run_ablation_experiment(
        contexts_df=small_contexts,
        repetitions=3,
        base_seed=42,
    )

    full_row = df_summary[df_summary["variant_id"] == "full_corrected"].iloc[0]
    unpad_row = df_summary[df_summary["variant_id"] == "unpadded_zero_margin"].iloc[0]

    assert full_row["overall_quality_compliance_pct"] >= unpad_row["overall_quality_compliance_pct"], (
        f"Full corrected ({full_row['overall_quality_compliance_pct']:.2f}%) should be >= "
        f"unpadded ({unpad_row['overall_quality_compliance_pct']:.2f}%)"
    )


# ==============================================================================
# 7. Trade-offs & Failure Analysis Tests
# ==============================================================================

def test_failure_analysis_output_structure(gate4_evaluator, small_contexts):
    """analyze_failures_and_tradeoffs must return dicts with expected top-level keys."""
    df_raw, df_summary, _ = gate4_evaluator.run_ablation_experiment(
        contexts_df=small_contexts,
        repetitions=2,
        base_seed=42,
    )
    tradeoffs, failures = gate4_evaluator.analyze_failures_and_tradeoffs(df_raw, df_summary)

    assert "tradeoffs_matrix" in tradeoffs
    assert len(tradeoffs["tradeoffs_matrix"]) == len(df_summary)

    assert "recycled_quartile_failures" in failures
    assert "moisture_failures" in failures
    assert "actuator_audit" in failures


def test_failure_analysis_tradeoffs_matrix_fields(gate4_evaluator, small_contexts):
    """Each trade-off matrix row must include required quantitative fields."""
    df_raw, df_summary, _ = gate4_evaluator.run_ablation_experiment(
        contexts_df=small_contexts,
        repetitions=2,
        base_seed=42,
    )
    tradeoffs, _ = gate4_evaluator.analyze_failures_and_tradeoffs(df_raw, df_summary)

    for t in tradeoffs["tradeoffs_matrix"]:
        assert "variant_id" in t
        assert "energy_reduction_pct" in t
        assert "quality_compliance_pct" in t
        assert "defect_count" in t
        assert "runtime_mean_ms" in t
        assert "runtime_p95_ms" in t
        assert "energy_variability_std_kwh" in t
        assert "tensile_margin_over_spec_min" in t


def test_actuator_audit_all_variants_within_bounds(gate4_evaluator, small_contexts):
    """Actuator audit must confirm all variants are within hard machine limits."""
    df_raw, df_summary, _ = gate4_evaluator.run_ablation_experiment(
        contexts_df=small_contexts,
        repetitions=2,
        base_seed=42,
    )
    _, failures = gate4_evaluator.analyze_failures_and_tradeoffs(df_raw, df_summary)

    for var_id, audit in failures["actuator_audit"].items():
        assert audit["all_actuators_within_hard_bounds"] is True, (
            f"Variant '{var_id}' has actuator violations in audit"
        )
        assert audit["min_melt_temp_c"] >= 205.0 - 1e-3
        assert audit["max_melt_temp_c"] <= 255.0 + 1e-3
        assert audit["min_injection_pressure_mpa"] >= 65.0 - 1e-3
        assert audit["max_injection_pressure_mpa"] <= 145.0 + 1e-3
        assert audit["min_cooling_time_s"] >= 12.0 - 1e-3
        assert audit["max_cooling_time_s"] <= 32.0 + 1e-3


def test_recycled_quartile_failure_all_variants_present(gate4_evaluator, small_contexts):
    """Recycled quartile failure dict must include all ablation variant IDs."""
    df_raw, df_summary, _ = gate4_evaluator.run_ablation_experiment(
        contexts_df=small_contexts,
        repetitions=2,
        base_seed=42,
    )
    _, failures = gate4_evaluator.analyze_failures_and_tradeoffs(df_raw, df_summary)

    expected_variants = set(df_summary["variant_id"].tolist())
    actual_variants = set(failures["recycled_quartile_failures"].keys())
    assert expected_variants == actual_variants


# ==============================================================================
# 8. Gate4SummaryResult Tests
# ==============================================================================

def test_gate4_summary_result_to_dict_is_serializable(gate4_evaluator, small_contexts):
    """Gate4SummaryResult.to_dict() must produce a fully JSON-serializable structure."""
    df_raw, df_summary, ablation_dict = gate4_evaluator.run_ablation_experiment(
        contexts_df=small_contexts,
        repetitions=2,
        base_seed=42,
    )
    tradeoffs, failures = gate4_evaluator.analyze_failures_and_tradeoffs(df_raw, df_summary)

    dummy_rob = {"noise_level_evaluations": {}, "seed_stability_evaluations": {}, "total_cycles": 0}
    dummy_sens = {"tensile_margin_sweep": {}, "recycled_content_sweep": {}, "total_cycles": 0}

    result = Gate4SummaryResult(
        metadata={"milestone": "Gate 4"},
        robustness_summary=dummy_rob,
        sensitivity_summary=dummy_sens,
        ablation_summary=ablation_dict,
        tradeoffs_summary=tradeoffs,
        failure_analysis=failures,
        actuator_safety_verification=failures["actuator_audit"],
    )

    d = result.to_dict()
    json_str = json.dumps(d)
    assert len(json_str) > 0
    parsed = json.loads(json_str)
    assert parsed["metadata"]["milestone"] == "Gate 4"


# ==============================================================================
# 9. End-to-End Runner Smoke Test
# ==============================================================================

def test_run_gate4_evaluation_smoke():
    """Verify run_gate4_evaluation executes end-to-end and returns exit code 0."""
    with tempfile.TemporaryDirectory() as temp_dir:
        exit_code, artifacts, results = run_gate4_evaluation(
            contexts_count=5,
            repetitions=2,
            base_seed=42,
            output_dir=temp_dir,
        )

        assert exit_code == 0

        # Verify all output artifacts were created
        for key, path in artifacts.items():
            assert os.path.exists(path), f"Artifact '{key}' not found at: {path}"

        # Verify JSON config content
        with open(artifacts["config"], "r", encoding="utf-8") as f:
            cfg = json.load(f)
        assert cfg["milestone"] == "Gate 4 - Robustness and Ablation Evaluation"
        assert cfg["contexts_count"] == 5
        assert cfg["repetitions_per_context"] == 2

        # Verify ablation summary CSV
        df_abl = pd.read_csv(artifacts["ablation_summary"])
        expected_variants = {
            "full_corrected", "no_recycled_protection", "initial_baseline_margin",
            "candidate_margin_120", "unpadded_zero_margin", "static_sop",
        }
        assert set(df_abl["variant_id"].tolist()) == expected_variants

        # Verify all ablation variants passed actuator safety check
        assert df_abl["actuator_limits_strictly_respected"].all()

        # Verify Gate 4 summary JSON
        with open(artifacts["summary_metrics"], "r", encoding="utf-8") as f:
            metrics = json.load(f)
        assert "metadata" in metrics
        assert "robustness_summary" in metrics
        assert "sensitivity_summary" in metrics
        assert "ablation_summary" in metrics
        assert "tradeoffs_summary" in metrics
        assert "failure_analysis" in metrics
        assert "actuator_safety_verification" in metrics

        # Verify Markdown report
        with open(artifacts["comparison_report"], "r", encoding="utf-8") as f:
            md_text = f.read()
        assert "# Gate 4: Robustness and Ablation Evaluation Report" in md_text
        assert "Ablation Study" in md_text
        assert "Robustness Testing" in md_text
        assert "Sensitivity Analysis" in md_text
        assert "Actuator Limits" in md_text

        # Verify core Gate 4 results object structure
        assert isinstance(results, Gate4SummaryResult)
        assert "noise_level_evaluations" in results.robustness_summary
        assert "tensile_margin_sweep" in results.sensitivity_summary
        assert "variants_evaluated" in results.ablation_summary
        assert results.metadata["contexts_count"] == 5