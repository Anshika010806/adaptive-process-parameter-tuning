"""
Systematic Validation Package for Adaptive Process Parameter Tuning.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 3 - Systematic Validation)
"""

from .evaluator import (
    Gate3Evaluator,
    EvaluationRecord,
    Gate3ValidationSummary,
    compute_confidence_interval
)
from .gate4_evaluator import (
    Gate4Evaluator,
    AblationVariantConfig,
    Gate4SummaryResult
)

__all__ = [
    "Gate3Evaluator",
    "EvaluationRecord",
    "Gate3ValidationSummary",
    "compute_confidence_interval",
    "Gate4Evaluator",
    "AblationVariantConfig",
    "Gate4SummaryResult"
]
