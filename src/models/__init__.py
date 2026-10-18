"""
Surrogate modeling and baseline package.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
"""

from .baseline import BaselineRegressor, BaselineMetrics
from .surrogate_benchmark import SurrogateBenchmark, SurrogateEvaluationResult

__all__ = [
    "BaselineRegressor",
    "BaselineMetrics",
    "SurrogateBenchmark",
    "SurrogateEvaluationResult"
]

