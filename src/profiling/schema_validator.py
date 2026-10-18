"""
Schema Validator and Scientific Guardrails Engine (Mode B).

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from .dataset_profiler import DatasetProfile


@dataclass
class SchemaMapping:
    """User-confirmed column assignment mapping."""
    target_column: str
    feature_columns: List[str]
    controllable_columns: List[str] = field(default_factory=list)
    identifier_columns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_column": self.target_column,
            "feature_columns": self.feature_columns,
            "controllable_columns": self.controllable_columns,
            "identifier_columns": self.identifier_columns,
        }


@dataclass
class ValidationResult:
    """Result of schema validation and capability assessment."""
    is_valid: bool
    task_type: str  # 'regression', 'unsupported'
    supports_prediction: bool
    supports_optimization: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    scientific_limitations: List[str] = field(default_factory=list)
    clean_sample_count: int = 0
    numeric_features: List[str] = field(default_factory=list)
    categorical_features: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "task_type": self.task_type,
            "supports_prediction": self.supports_prediction,
            "supports_optimization": self.supports_optimization,
            "errors": self.errors,
            "warnings": self.warnings,
            "scientific_limitations": self.scientific_limitations,
            "clean_sample_count": self.clean_sample_count,
            "numeric_features": self.numeric_features,
            "categorical_features": self.categorical_features,
        }


class SchemaValidator:
    """
    Validates user schema configurations and assesses scientific capabilities.
    Enforces that optimization is only enabled when genuine controllable parameters exist
    and logs observational confounding warnings.
    """

    MIN_SAMPLES = 15

    def validate(
        self,
        df: pd.DataFrame,
        mapping: SchemaMapping,
        profile: Optional[DatasetProfile] = None
    ) -> ValidationResult:
        """
        Validate schema mappings defensively against DataFrame.
        """
        errors: List[str] = []
        warnings: List[str] = []
        limitations: List[str] = []

        # 1. Target Column Validation
        target = mapping.target_column
        if not target or target not in df.columns:
            errors.append(f"Target column '{target}' does not exist in the dataset.")
            return ValidationResult(
                is_valid=False,
                task_type="unsupported",
                supports_prediction=False,
                supports_optimization=False,
                errors=errors
            )

        target_series = df[target]
        valid_targets = target_series.dropna()
        if len(valid_targets) < self.MIN_SAMPLES:
            errors.append(
                f"Target column '{target}' contains only {len(valid_targets)} non-null values. "
                f"At least {self.MIN_SAMPLES} valid samples are required."
            )

        if not pd.api.types.is_numeric_dtype(target_series):
            errors.append(
                f"Target column '{target}' is non-numeric (type: {target_series.dtype}). "
                "Only continuous numeric regression targets are currently supported in this worklet."
            )

        if len(valid_targets) > 0 and valid_targets.nunique() <= 1:
            errors.append(f"Target column '{target}' has zero variance (constant value). Cannot fit regression.")

        # 2. Features Validation
        features = [f for f in mapping.feature_columns if f != target]
        if not features:
            errors.append("No valid input feature columns selected. At least one feature column is required.")

        missing_features = [f for f in features if f not in df.columns]
        if missing_features:
            errors.append(f"Selected feature columns not found in dataset: {missing_features}")

        # Check for target leakage in features
        if target in mapping.feature_columns:
            warnings.append(f"Target column '{target}' was found in feature list and was automatically removed to prevent target leakage.")

        # Classify features as numeric vs categorical
        num_features = []
        cat_features = []
        for f in features:
            if f in df.columns:
                if pd.api.types.is_numeric_dtype(df[f]):
                    if df[f].nunique() <= 1:
                        warnings.append(f"Feature '{f}' has zero variance and provides no predictive information.")
                    num_features.append(f)
                else:
                    cat_features.append(f)

        # 3. Clean Sample Count (rows with non-null target)
        clean_samples = len(valid_targets)

        # If errors exist up to here, validation fails
        if errors:
            return ValidationResult(
                is_valid=False,
                task_type="unsupported",
                supports_prediction=False,
                supports_optimization=False,
                errors=errors,
                warnings=warnings,
                clean_sample_count=clean_samples,
                numeric_features=num_features,
                categorical_features=cat_features
            )

        # 4. Controllable Parameter Assessment (Optimization vs Prediction)
        controls = mapping.controllable_columns
        supports_opt = False

        if not controls:
            supports_opt = False
            limitations.append(
                "No controllable machine parameters mapped. Adaptive optimization is disabled; "
                "the dataset supports supervised predictive modeling only."
            )
        else:
            invalid_controls = [c for c in controls if c not in features]
            if invalid_controls:
                errors.append(f"Controllable parameters must be part of selected features: {invalid_controls}")
            
            non_numeric_controls = [c for c in controls if c in df.columns and not pd.api.types.is_numeric_dtype(df[c])]
            if non_numeric_controls:
                errors.append(f"Controllable parameters must be numeric actuators: {non_numeric_controls}")

            if not errors:
                supports_opt = True
                limitations.append(
                    "Scientific Notice on Observational Optimization: This dataset is purely observational. "
                    "Optimizing parameters over learned statistical correlations assumes unconfoundedness "
                    "and absence of unobserved shop-floor disturbances. Recommendations should be validated "
                    "with physical trial runs before deployment."
                )

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            task_type="regression" if is_valid else "unsupported",
            supports_prediction=is_valid,
            supports_optimization=supports_opt and is_valid,
            errors=errors,
            warnings=warnings,
            scientific_limitations=limitations,
            clean_sample_count=clean_samples,
            numeric_features=num_features,
            categorical_features=cat_features
        )
