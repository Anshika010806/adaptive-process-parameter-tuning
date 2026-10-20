"""
Domain Guard for Manufacturing Input Validation and Out-of-Distribution (OOD) Detection.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 2)
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class GuardResult:
    """Immutable outcome of domain validation and support check."""
    is_valid: bool          # Physically valid (non-negative, non-NaN, physical bounds)
    is_in_support: bool     # Within training distribution support envelope
    is_feasible: bool       # Whether adaptive tuning can proceed safely
    status: str             # 'VALID', 'INVALID_INPUT', 'OOD_REJECTED', 'INFEASIBLE'
    message: str            # Detailed human-readable explanation
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DomainGuard:
    """
    Validates material input covariates and enforces domain boundary defenses.

    Defends against:
    1. Unphysical or corrupted inputs (NaN, Inf, negative moisture/MFI/recycled pct).
    2. Out-of-Distribution (OOD) conditions beyond surrogate training support:
       - moisture_pct: [0.05, 0.50] wt%
       - melt_flow_index: [14.0, 30.0] g/10 min
       - ambient_temp_c: [16.0, 32.0] deg C
       - recycled_pct: [10.0, 40.0] wt%
    3. Uncompensable degradation regimes where quality specs are mathematically
       unreachable even with maximum actuator compensation:
       - moisture_pct > 0.55 wt% (extreme volatile voiding)
       - moisture_pct > 0.45 wt% and recycled_pct > 38.0 wt% (compound degradation)

    Policy:
    - Never silently clip inputs.
    - Reject OOD inputs by default with explicit status 'OOD_REJECTED'.
    - Never trust unsupported surrogate predictions outside the training envelope.
    """

    DEFAULT_TRAIN_SUPPORT = {
        "moisture_pct": (0.05, 0.50),
        "melt_flow_index": (14.0, 30.0),
        "ambient_temp_c": (16.0, 32.0),
        "recycled_pct": (10.0, 40.0)
    }

    PHYSICAL_BOUNDS = {
        "moisture_pct": (0.0, 10.0),
        "melt_flow_index": (0.001, 100.0),
        "ambient_temp_c": (-50.0, 70.0),
        "recycled_pct": (0.0, 100.0)
    }

    def __init__(
        self,
        config_path: Optional[str] = None,
        reject_ood: bool = True
    ):
        self.reject_ood = reject_ood
        self.support_bounds = dict(self.DEFAULT_TRAIN_SUPPORT)

        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, "config", "simulation_config.json")

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            mat_cfg = cfg.get("material_inputs", {})
            for key in ["moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct"]:
                if key in mat_cfg and "train_min" in mat_cfg[key] and "train_max" in mat_cfg[key]:
                    self.support_bounds[key] = (
                        float(mat_cfg[key]["train_min"]),
                        float(mat_cfg[key]["train_max"])
                    )

    def validate_material(
        self,
        moisture_pct: float,
        melt_flow_index: float,
        ambient_temp_c: float,
        recycled_pct: float
    ) -> GuardResult:
        """
        Validate single-cycle material disturbance inputs.
        """
        inputs = {
            "moisture_pct": moisture_pct,
            "melt_flow_index": melt_flow_index,
            "ambient_temp_c": ambient_temp_c,
            "recycled_pct": recycled_pct
        }

        # 1. Check non-finite / non-numeric
        for name, val in inputs.items():
            try:
                f_val = float(val)
                if np.isnan(f_val) or np.isinf(f_val):
                    return GuardResult(
                        is_valid=False,
                        is_in_support=False,
                        is_feasible=False,
                        status="INVALID_INPUT",
                        message=f"Input '{name}' is non-finite: {val}",
                        violations=[f"{name}={val} (non-finite)"]
                    )
                inputs[name] = f_val
            except (ValueError, TypeError):
                return GuardResult(
                    is_valid=False,
                    is_in_support=False,
                    is_feasible=False,
                    status="INVALID_INPUT",
                    message=f"Input '{name}' cannot be cast to float: {val}",
                    violations=[f"{name}={val} (non-numeric)"]
                )

        m = inputs["moisture_pct"]
        mfi = inputs["melt_flow_index"]
        t_amb = inputs["ambient_temp_c"]
        rec = inputs["recycled_pct"]

        # 2. Check fundamental physical bounds (non-negativity, sensor limits)
        phys_violations = []
        for name, (low, high) in self.PHYSICAL_BOUNDS.items():
            v = inputs[name]
            if v < low or v > high:
                phys_violations.append(f"{name}={v:.3f} outside physical bounds [{low}, {high}]")

        if phys_violations:
            return GuardResult(
                is_valid=False,
                is_in_support=False,
                is_feasible=False,
                status="INVALID_INPUT",
                message=f"Physical domain violation: {'; '.join(phys_violations)}",
                violations=phys_violations
            )

        # 3. Check extreme uncompensable physics regimes
        if m > 0.55:
            return GuardResult(
                is_valid=True,
                is_in_support=False,
                is_feasible=False,
                status="INFEASIBLE",
                message=f"Extremely high moisture ({m:.3f} wt% > 0.55 wt%) causes severe voiding that cannot be compensated within machine limits.",
                violations=[f"moisture_pct={m:.3f} > 0.55 wt% (uncompensable voiding)"]
            )

        if m > 0.45 and rec > 38.0:
            return GuardResult(
                is_valid=True,
                is_in_support=False,
                is_feasible=False,
                status="INFEASIBLE",
                message=f"Combined high moisture ({m:.2f}%) and high recycled content ({rec:.1f}%) exceeds compensable operating envelope.",
                violations=[f"moisture_pct={m:.2f}% and recycled_pct={rec:.1f}% (compound degradation)"]
            )

        # 4. Check surrogate training distribution support bounds (OOD detection)
        support_violations = []
        for name, (train_min, train_max) in self.support_bounds.items():
            v = inputs[name]
            if v < train_min or v > train_max:
                support_violations.append(
                    f"{name}={v:.3f} outside training support [{train_min:.2f}, {train_max:.2f}]"
                )

        if support_violations:
            if self.reject_ood:
                return GuardResult(
                    is_valid=True,
                    is_in_support=False,
                    is_feasible=False,
                    status="OOD_REJECTED",
                    message=f"Out-of-training-support: {'; '.join(support_violations)}. Rejected by domain guard.",
                    violations=support_violations
                )
            else:
                return GuardResult(
                    is_valid=True,
                    is_in_support=False,
                    is_feasible=True,
                    status="OOD_WARNING",
                    message=f"Out-of-training-support: {'; '.join(support_violations)}. Proceeding with extrapolation caution.",
                    violations=support_violations
                )

        # 5. Passed all checks
        return GuardResult(
            is_valid=True,
            is_in_support=True,
            is_feasible=True,
            status="VALID",
            message="Material condition within compensable envelope and training support.",
            violations=[]
        )

    def validate_batch(self, df: pd.DataFrame) -> List[GuardResult]:
        """Validate an entire tabular batch of material disturbance cycles."""
        material_cols = ["moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct"]
        missing = [c for c in material_cols if c not in df.columns]
        if missing:
            raise KeyError(f"DataFrame is missing required material columns: {missing}")

        results = []
        for _, row in df.iterrows():
            res = self.validate_material(
                moisture_pct=row["moisture_pct"],
                melt_flow_index=row["melt_flow_index"],
                ambient_temp_c=row["ambient_temp_c"],
                recycled_pct=row["recycled_pct"]
            )
            results.append(res)
        return results
