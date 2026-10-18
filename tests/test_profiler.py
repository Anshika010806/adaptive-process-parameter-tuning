"""
Unit Tests for Dataset Profiler, Schema Validator, and Dynamic Pipeline (Mode B).

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
from src.profiling.dataset_profiler import DatasetProfiler, DatasetProfile
from src.profiling.schema_validator import SchemaValidator, SchemaMapping, ValidationResult
from src.profiling.dynamic_pipeline import DynamicPipelineBuilder, EvaluationMetrics


@pytest.fixture
def profiler():
    return DatasetProfiler()


@pytest.fixture
def validator():
    return SchemaValidator()


@pytest.fixture
def sample_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "examiner_samples")


# ============================================================================
# 1. Chemical Reactor Dataset Tests (CSV, All-Continuous Features)
# ============================================================================

def test_profile_chemical_reactor_csv(profiler, sample_dir):
    """Verify loading and profiling of continuous CSV dataset."""
    csv_path = os.path.join(sample_dir, "examiner_chemical_reactor.csv")
    df = profiler.load_file(csv_path)

    assert len(df) == 400
    assert "reaction_yield_pct" in df.columns

    profile = profiler.profile(df, filename="examiner_chemical_reactor.csv")
    assert profile.total_rows == 400
    assert profile.total_columns == 7
    assert "batch_id" in profile.candidate_identifiers
    assert "reaction_yield_pct" in profile.candidate_targets


def test_dynamic_pipeline_chemical_reactor(profiler, validator, sample_dir):
    """Verify dynamic pipeline fits and evaluates cleanly on chemical dataset."""
    csv_path = os.path.join(sample_dir, "examiner_chemical_reactor.csv")
    df = profiler.load_file(csv_path)
    profile = profiler.profile(df)

    mapping = SchemaMapping(
        target_column="reaction_yield_pct",
        feature_columns=["reagent_temp_c", "catalyst_flow_lpm", "feed_purity_pct", "reactor_pressure_bar", "agitation_rpm"],
        controllable_columns=["catalyst_flow_lpm", "reagent_temp_c"],
        identifier_columns=["batch_id"]
    )

    val_res = validator.validate(df, mapping, profile)
    assert val_res.is_valid is True
    assert val_res.supports_prediction is True
    assert val_res.supports_optimization is True

    builder = DynamicPipelineBuilder(val_res)
    pipe, metrics, eval_df = builder.fit_and_evaluate(df, mapping, test_size=0.25, random_state=42)

    assert metrics.n_train == 300
    assert metrics.n_test == 100
    assert metrics.mae > 0.0
    assert metrics.r2 > 0.70  # Learned genuine relationship
    assert len(eval_df) == 100


# ============================================================================
# 2. Machining Wear Dataset Tests (Excel .xlsx, Missing Values, Categorical)
# ============================================================================

def test_profile_machining_wear_excel(profiler, sample_dir):
    """Verify Excel parsing, categorical detection, and missing value profiling."""
    xlsx_path = os.path.join(sample_dir, "examiner_machining_wear.xlsx")
    df = profiler.load_file(xlsx_path)

    assert len(df) == 250
    profile = profiler.profile(df, filename="examiner_machining_wear.xlsx")

    # Missing value checks
    assert profile.columns["feed_rate_mmpm"].missing_count > 0
    assert profile.columns["tool_grade"].missing_count > 0

    # Categorical detection
    assert profile.columns["tool_grade"].inferred_type == "categorical"
    assert profile.columns["coolant_type"].inferred_type == "categorical"


def test_dynamic_pipeline_handles_missing_and_unseen_categories(profiler, validator, sample_dir):
    """Verify pipeline handles imputation and unseen categorical levels gracefully."""
    xlsx_path = os.path.join(sample_dir, "examiner_machining_wear.xlsx")
    df = profiler.load_file(xlsx_path)
    profile = profiler.profile(df)

    mapping = SchemaMapping(
        target_column="surface_roughness_ra",
        feature_columns=["tool_grade", "feed_rate_mmpm", "spindle_rpm", "vibration_rms_g", "coolant_type"],
        identifier_columns=["component_serial"]
    )

    val_res = validator.validate(df, mapping, profile)
    assert val_res.is_valid is True

    builder = DynamicPipelineBuilder(val_res)
    pipe, metrics, _ = builder.fit_and_evaluate(df, mapping, test_size=0.20, random_state=42)

    assert metrics.n_train == 200
    assert metrics.n_test == 50
    assert metrics.r2 > 0.60

    # Test previously unseen category level at inference time (Must NOT crash)
    unseen_sample = pd.DataFrame([{
        "tool_grade": "BrandNew-Exotic-Grade",  # Level unseen during training
        "feed_rate_mmpm": 220.0,
        "spindle_rpm": 2500.0,
        "vibration_rms_g": 0.45,
        "coolant_type": "Cryogenic"  # Another unseen level
    }])
    pred = pipe.predict(unseen_sample)
    assert len(pred) == 1
    assert not np.isnan(pred[0])


# ============================================================================
# 3. Defensive Validation Tests (Malformed Dataset & Scientific Guardrails)
# ============================================================================

def test_defensive_validation_catches_constant_and_empty_columns(profiler, validator, sample_dir):
    """Verify profiler and validator catch constant and 100% missing columns."""
    csv_path = os.path.join(sample_dir, "examiner_malformed_unsupported.csv")
    df = profiler.load_file(csv_path)
    profile = profiler.profile(df)

    assert "constant_setting" in profile.candidate_constants
    assert profile.columns["all_empty_col"].inferred_type == "all_missing"

    # Attempting to use constant column as target must fail validation
    bad_mapping = SchemaMapping(
        target_column="constant_setting",
        feature_columns=["sensor_alpha"]
    )
    val_res = validator.validate(df, bad_mapping, profile)
    assert val_res.is_valid is False
    assert any("zero variance" in err for err in val_res.errors)


def test_defensive_validation_catches_target_leakage(validator):
    """Validator must strip target if accidentally placed in feature list."""
    dummy_df = pd.DataFrame({
        "feat_1": np.random.randn(50),
        "target_col": np.random.randn(50)
    })
    mapping = SchemaMapping(
        target_column="target_col",
        feature_columns=["feat_1", "target_col"]  # Leakage attempt
    )
    val_res = validator.validate(dummy_df, mapping)
    assert val_res.is_valid is True
    assert "target_col" not in val_res.numeric_features
    assert any("target leakage" in w for w in val_res.warnings)


def test_scientific_limitation_warning_on_purely_observational_data(validator):
    """Verify observational optimization warning is triggered when controls are mapped."""
    dummy_df = pd.DataFrame({
        "disturb_1": np.random.randn(50),
        "control_1": np.random.randn(50),
        "quality_y": np.random.randn(50)
    })
    mapping = SchemaMapping(
        target_column="quality_y",
        feature_columns=["disturb_1", "control_1"],
        controllable_columns=["control_1"]
    )
    val_res = validator.validate(dummy_df, mapping)
    assert val_res.is_valid is True
    assert val_res.supports_optimization is True
    assert any("Observational Optimization" in lim for lim in val_res.scientific_limitations)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main(["-v", __file__]))
