"""
Comprehensive Unit and Integration Tests for Gate 3: Systematic Validation.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 3 - Systematic Validation)
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
from src.optimization.surrogate_loader import load_or_train_surrogate
from src.optimization.adaptive_tuner import AdaptiveProcessTuner, TuningRecommendation
from src.optimization.simulator_validator import SimulatorValidator, SimulatorValidationResult
from src.validation.evaluator import (
    Gate3Evaluator,
    EvaluationRecord,
    Gate3ValidationSummary,
    compute_confidence_interval
)
from src.validation.run_gate3 import run_gate3_validation


@pytest.fixture(scope="module")
def shared_surrogate():
    """Load or train surrogate using training data exclusively."""
    return load_or_train_surrogate(model_name="RandomForest", random_state=42)


@pytest.fixture
def fast_tuner(shared_surrogate):
    """Instantiate fast AdaptiveProcessTuner with coarser candidate grid for snappy tests."""
    return AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        random_state=42,
        search_strategy="grid",
        grid_resolution=(7, 7, 5),
        reject_ood=True,
        refine_local=False
    )


@pytest.fixture
def evaluator(fast_tuner):
    """Instantiate Gate3Evaluator with fast tuner."""
    return Gate3Evaluator(tuner=fast_tuner)


# ==============================================================================
# 1. Reproducibility Tests
# ==============================================================================

def test_gate3_reproducibility_across_identical_seeds(shared_surrogate):
    """Verify identical random seeds produce identical evaluation records and summary metrics."""
    tuner1 = AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        random_state=42,
        grid_resolution=(7, 7, 5),
        refine_local=False
    )
    tuner2 = AdaptiveProcessTuner(
        surrogate_pipeline=shared_surrogate,
        random_state=42,
        grid_resolution=(7, 7, 5),
        refine_local=False
    )

    eval1 = Gate3Evaluator(tuner=tuner1)
    eval2 = Gate3Evaluator(tuner=tuner2)

    contexts1 = eval1.sample_contexts(n=5, seed=101)
    contexts2 = eval2.sample_contexts(n=5, seed=101)
    pd.testing.assert_frame_equal(contexts1, contexts2)

    _, sum1, df1 = eval1.evaluate_batch(contexts1, repetitions=2, base_seed=42, add_noise=True)
    _, sum2, df2 = eval2.evaluate_batch(contexts2, repetitions=2, base_seed=42, add_noise=True)

    compare_cols = [c for c in df1.columns if c != "optimization_latency_ms"]
    pd.testing.assert_frame_equal(df1[compare_cols], df2[compare_cols])
    assert (df1["optimization_latency_ms"] > 0).all()
    assert (df2["optimization_latency_ms"] > 0).all()
    assert sum1.energy_metrics["reduction_pct_mean"] == pytest.approx(sum2.energy_metrics["reduction_pct_mean"], abs=1e-7)
    assert sum1.compliance_metrics["tuned_overall_compliance_pct"] == pytest.approx(sum2.compliance_metrics["tuned_overall_compliance_pct"], abs=1e-7)


def test_gate3_sample_contexts_support_envelope(evaluator):
    """Verify that sampled evaluation contexts are strictly within documented training support."""
    df_contexts = evaluator.sample_contexts(n=25, seed=202)
    assert len(df_contexts) == 25

    guard = DomainGuard()
    for _, row in df_contexts.iterrows():
        res = guard.validate_material(
            moisture_pct=row["moisture_pct"],
            melt_flow_index=row["melt_flow_index"],
            ambient_temp_c=row["ambient_temp_c"],
            recycled_pct=row["recycled_pct"]
        )
        assert res.is_valid is True
        assert res.is_in_support is True
        assert res.is_feasible is True
        assert res.status == "VALID"


# ==============================================================================
# 2. Matched Baseline Comparison Tests
# ==============================================================================

def test_matched_noise_realizations_between_sop_and_tuner(evaluator):
    """Verify SOP baseline and adaptive recommendation experience identical noise realizations."""
    df_contexts = evaluator.sample_contexts(n=3, seed=55)
    records, _, _ = evaluator.evaluate_batch(df_contexts, repetitions=3, base_seed=42, add_noise=True)

    for rec in records:
        assert rec.matched_seed is not None
        # Verify baseline setpoint matches static SOP
        assert rec.baseline_melt_temp_c == 230.0
        assert rec.baseline_injection_pressure_mpa == 100.0
        assert rec.baseline_cooling_time_s == 20.0

        # Ground truth check with identical seed
        sim = PolymerInjectionSimulator()
        rng = np.random.default_rng(rec.matched_seed)
        expected_base = sim.evaluate_single(
            moisture_pct=rec.moisture_pct,
            melt_flow_index=rec.melt_flow_index,
            ambient_temp_c=rec.ambient_temp_c,
            recycled_pct=rec.recycled_pct,
            melt_temp_c=230.0,
            injection_pressure_mpa=100.0,
            cooling_time_s=20.0,
            add_noise=True,
            rng=rng
        )
        assert rec.sim_baseline_tensile_mpa == pytest.approx(expected_base.tensile_strength_mpa, abs=1e-7)
        assert rec.sim_baseline_shrinkage_pct == pytest.approx(expected_base.volumetric_shrinkage_pct, abs=1e-7)


# ==============================================================================
# 3. Metric Calculations & Confidence Interval Tests
# ==============================================================================

def test_compute_confidence_interval_math():
    """Verify confidence interval mathematics on known distributions."""
    # Constant data
    ci_const = compute_confidence_interval([5.0, 5.0, 5.0, 5.0])
    assert ci_const["mean"] == 5.0
    assert ci_const["std"] == 0.0
    assert ci_const["ci_lower"] == 5.0
    assert ci_const["ci_upper"] == 5.0

    # Single item
    ci_single = compute_confidence_interval([3.14])
    assert ci_single["mean"] == 3.14
    assert ci_single["ci_lower"] == 3.14
    assert ci_single["n"] == 1

    # Empty
    ci_empty = compute_confidence_interval([])
    assert ci_empty["n"] == 0
    assert ci_empty["mean"] == 0.0

    # Known array
    data = np.array([10.0, 12.0, 14.0, 16.0, 18.0])  # mean 14.0, std 3.162277, n=5, df=4
    ci = compute_confidence_interval(data, confidence=0.95)
    assert ci["mean"] == pytest.approx(14.0, abs=1e-5)
    assert ci["median"] == pytest.approx(14.0, abs=1e-5)
    assert ci["std"] == pytest.approx(np.std(data, ddof=1), abs=1e-5)
    assert ci["ci_lower"] < 14.0 < ci["ci_upper"]
    assert (ci["ci_upper"] - ci["mean"]) == pytest.approx(ci["ci_half_width"], abs=1e-5)


def test_energy_reduction_metric_calculation(evaluator):
    """Verify energy reduction kWh and percentage arithmetic are strictly accurate."""
    df_contexts = evaluator.sample_contexts(n=4, seed=77)
    records, summary, _ = evaluator.evaluate_batch(df_contexts, repetitions=1, base_seed=42, add_noise=False)

    for r in records:
        if r.tuner_feasible:
            expected_saved_kwh = r.sim_baseline_energy_kwh - r.sim_tuned_energy_kwh
            expected_saved_pct = (expected_saved_kwh / r.sim_baseline_energy_kwh) * 100.0
            assert r.energy_reduction_kwh == pytest.approx(expected_saved_kwh, abs=1e-6)
            assert r.energy_reduction_pct == pytest.approx(expected_saved_pct, abs=1e-6)


def test_surrogate_prediction_errors_recorded(evaluator):
    """Verify surrogate prediction errors match absolute difference with simulator ground truth."""
    df_contexts = evaluator.sample_contexts(n=3, seed=88)
    records, summary, _ = evaluator.evaluate_batch(df_contexts, repetitions=1, base_seed=42, add_noise=False)

    for r in records:
        if r.tuner_feasible:
            assert r.tensile_abs_error_mpa == pytest.approx(abs(r.surrogate_pred_tensile_mpa - r.sim_tuned_tensile_mpa), abs=1e-6)
            assert r.shrinkage_abs_error_pct == pytest.approx(abs(r.surrogate_pred_shrinkage_pct - r.sim_tuned_shrinkage_pct), abs=1e-6)
            assert r.energy_abs_error_kwh == pytest.approx(abs(r.surrogate_pred_energy_kwh - r.sim_tuned_energy_kwh), abs=1e-6)


# ==============================================================================
# 4. Quality Violation & Specification Compliance Tests
# ==============================================================================

def test_quality_violation_rate_calculation(evaluator):
    """Verify quality violation rate is tracked accurately and matches (100 - compliance rate)."""
    df_contexts = evaluator.sample_contexts(n=5, seed=99)
    _, summary, records_df = evaluator.evaluate_batch(df_contexts, repetitions=2, base_seed=42, add_noise=True)

    base_viol_rate = summary.quality_violation_metrics["baseline_quality_violation_rate_pct"]
    base_comp_rate = summary.compliance_metrics["baseline_overall_compliance_pct"]
    assert base_viol_rate == pytest.approx(100.0 - base_comp_rate, abs=1e-5)

    if summary.feasibility_metrics["feasible_count"] > 0:
        tuned_viol_rate = summary.quality_violation_metrics["tuned_quality_violation_rate_pct"]
        tuned_comp_rate = summary.compliance_metrics["tuned_overall_compliance_pct"]
        assert tuned_viol_rate == pytest.approx(100.0 - tuned_comp_rate, abs=1e-5)


# ==============================================================================
# 5. Failure and OOD Robustness Handling Tests
# ==============================================================================

def test_failure_handling_on_ood_contexts(evaluator):
    """Verify out-of-distribution contexts are rejected safely without crashing or claiming savings."""
    ood_contexts = pd.DataFrame({
        "context_id": [0, 1],
        "moisture_pct": [0.55, 0.15],        # 0.55 is OOD moisture
        "melt_flow_index": [22.0, 35.0],      # 35.0 is OOD MFI
        "ambient_temp_c": [24.0, 36.5],       # 36.5 is OOD heatwave
        "recycled_pct": [25.0, 25.0]
    })

    records, summary, records_df = evaluator.evaluate_batch(
        ood_contexts,
        repetitions=2,
        base_seed=42,
        add_noise=False
    )

    assert len(records) == 4
    for r in records:
        assert r.tuner_feasible is False
        assert r.tuner_status in ["OOD_REJECTED", "INFEASIBLE"]
        assert r.tuned_melt_temp_c is None
        assert r.deployed_melt_temp_c == 230.0  # SOP fallback
        assert r.deployed_injection_pressure_mpa == 100.0
        assert r.deployed_cooling_time_s == 20.0
        assert r.energy_reduction_kwh == 0.0
        assert r.energy_reduction_pct == 0.0

    assert summary.feasibility_metrics["feasible_count"] == 0
    assert summary.feasibility_metrics["infeasible_count"] == 4


def test_failure_handling_on_invalid_inputs(evaluator):
    """Verify unphysical inputs (negative values, NaNs) are flagged as INVALID_INPUT."""
    corrupted_contexts = pd.DataFrame({
        "context_id": [0],
        "moisture_pct": [-0.10],
        "melt_flow_index": [22.0],
        "ambient_temp_c": [24.0],
        "recycled_pct": [25.0]
    })

    records, summary, _ = evaluator.evaluate_batch(corrupted_contexts, repetitions=1, base_seed=42)
    assert records[0].tuner_status == "INVALID_INPUT"
    assert records[0].tuner_feasible is False
    assert records[0].energy_reduction_kwh == 0.0


# ==============================================================================
# 6. Report Generation & Schema Tests
# ==============================================================================

def test_report_generation_file_creation_and_schema(evaluator):
    """Verify that evaluator generates valid JSON, CSV, and Markdown reports."""
    df_contexts = evaluator.sample_contexts(n=4, seed=12)
    records, summary, records_df = evaluator.evaluate_batch(df_contexts, repetitions=2, base_seed=42)

    with tempfile.TemporaryDirectory() as temp_dir:
        report_paths = evaluator.save_reports(summary, records_df, output_dir=temp_dir)

        # Check all files exist
        assert os.path.exists(report_paths["json"])
        assert os.path.exists(report_paths["csv_records"])
        assert os.path.exists(report_paths["csv_summary"])
        assert os.path.exists(report_paths["markdown"])

        # Validate JSON content
        with open(report_paths["json"], "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["metadata"]["milestone"] == "Gate 3 - Systematic Validation"
        assert data["sample_counts"]["n_contexts"] == 4
        assert data["sample_counts"]["repetitions_per_context"] == 2
        assert data["sample_counts"]["total_cycle_evaluations"] == 8
        assert "energy_metrics" in data
        assert "compliance_metrics" in data
        assert "surrogate_prediction_errors" in data
        assert "latency_and_compute_metrics" in data

        # Validate CSV content
        df_rec = pd.read_csv(report_paths["csv_records"])
        assert len(df_rec) == 8
        assert "energy_reduction_pct" in df_rec.columns
        assert "sim_baseline_energy_kwh" in df_rec.columns

        df_sum = pd.read_csv(report_paths["csv_summary"])
        assert len(df_sum) > 15
        assert "metric" in df_sum.columns
        assert "value" in df_sum.columns

        # Validate Markdown content
        with open(report_paths["markdown"], "r", encoding="utf-8") as f:
            md_text = f.read()

        assert "# Gate 3 — Systematic Validation & Matched-Baseline Evaluation Report" in md_text
        assert "Executive Summary" in md_text
        assert "Matched Baseline Comparison" in md_text
        assert "Surrogate Prediction Fidelity" in md_text
        assert "Engineering Limitations & Guardrail Discussion" in md_text


# ==============================================================================
# 7. End-to-End CLI Smoke Test
# ==============================================================================

def test_run_gate3_validation_end_to_end():
    """Verify run_gate3_validation executes end-to-end and returns exit code 0."""
    with tempfile.TemporaryDirectory() as temp_dir:
        exit_code, report_paths, summary = run_gate3_validation(
            contexts_count=4,
            repetitions=2,
            seed=42,
            model_type="RandomForest",
            search_strategy="grid",
            output_dir=temp_dir,
            add_noise=True,
            reject_ood=True
        )

        assert exit_code == 0
        assert os.path.exists(report_paths["json"])
        assert os.path.exists(report_paths["csv_records"])
        assert os.path.exists(report_paths["csv_summary"])
        assert os.path.exists(report_paths["markdown"])

        assert summary.sample_counts["n_contexts"] == 4
        assert summary.sample_counts["total_cycle_evaluations"] == 8
        assert summary.energy_metrics["reduction_pct_mean"] > 0.0
        assert summary.latency_and_compute_metrics["simulator_evals_during_optimization"] == 0
