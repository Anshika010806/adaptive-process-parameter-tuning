"""
Authoritative Simulator Validation and Matched-Baseline Evaluation for Gate 2.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 2)
"""

from __future__ import annotations
import os
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import numpy as np

from src.simulation.process_simulator import PolymerInjectionSimulator, SimulationResult
from src.optimization.static_controller import StaticSOPController
from .adaptive_tuner import TuningRecommendation


@dataclass(frozen=True)
class SimulatorValidationResult:
    """Rigorous evaluation comparing surrogate predictions and simulator ground truth."""
    is_feasible: bool
    status: str
    message: str
    material_inputs: Dict[str, float]
    actuators_tuned: Optional[Dict[str, float]]
    actuators_baseline: Dict[str, float]
    surrogate_predicted: Optional[Dict[str, Any]]
    simulated_tuned: Optional[Dict[str, Any]]
    simulated_baseline: Dict[str, Any]
    energy_baseline_kwh: float
    energy_tuned_kwh: Optional[float]
    energy_reduction_kwh: Optional[float]
    energy_reduction_pct: Optional[float]
    tensile_prediction_error: Optional[float]
    shrinkage_prediction_error: Optional[float]
    realized_in_spec: bool
    tensile_spec_met: bool
    shrinkage_spec_met: bool
    matched_noise_seed: Optional[int]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SimulatorValidator:
    """
    Validates adaptive tuning recommendations against the authoritative physical simulator.

    Core Scientific Guardrails:
    1. Independent True Simulator: Ground truth physics are decoupled from ML surrogates.
    2. Matched Noise Realizations: When stochastic noise is evaluated, identical noise sequences
       are injected into both baseline and tuned runs for an unbiased matched-pair comparison.
    3. Separate Reporting: Surrogate predictions and simulator outcomes are recorded separately.
    4. Failure Integrity: Infeasible or rejected candidates return explicit failure statuses
       without claiming valid manufacturing improvements.
    """

    def __init__(
        self,
        simulator: Optional[PolymerInjectionSimulator] = None,
        static_controller: Optional[StaticSOPController] = None
    ):
        self.simulator = simulator or PolymerInjectionSimulator()
        self.static_controller = static_controller or StaticSOPController()

    def validate(
        self,
        recommendation: TuningRecommendation,
        moisture_pct: float,
        melt_flow_index: float,
        ambient_temp_c: float,
        recycled_pct: float,
        seed: Optional[int] = 42,
        add_noise: bool = False
    ) -> SimulatorValidationResult:
        """
        Execute matched-pair evaluation of baseline SOP vs tuned setpoints in the simulator.
        """
        material_inputs = {
            "moisture_pct": float(moisture_pct),
            "melt_flow_index": float(melt_flow_index),
            "ambient_temp_c": float(ambient_temp_c),
            "recycled_pct": float(recycled_pct)
        }

        actuators_baseline = {
            "melt_temp_c": self.static_controller.melt_temp_c,
            "injection_pressure_mpa": self.static_controller.injection_pressure_mpa,
            "cooling_time_s": self.static_controller.cooling_time_s
        }

        # 1. Evaluate baseline in true simulator
        rng_base = np.random.default_rng(seed) if (add_noise and seed is not None) else None
        res_baseline = self.simulator.evaluate_single(
            moisture_pct=moisture_pct,
            melt_flow_index=melt_flow_index,
            ambient_temp_c=ambient_temp_c,
            recycled_pct=recycled_pct,
            melt_temp_c=actuators_baseline["melt_temp_c"],
            injection_pressure_mpa=actuators_baseline["injection_pressure_mpa"],
            cooling_time_s=actuators_baseline["cooling_time_s"],
            add_noise=add_noise,
            rng=rng_base
        )
        base_dict = res_baseline.to_dict()

        # 2. Check if recommendation is feasible
        if not recommendation.is_feasible:
            return SimulatorValidationResult(
                is_feasible=False,
                status=recommendation.status,
                message=recommendation.message,
                material_inputs=material_inputs,
                actuators_tuned=None,
                actuators_baseline=actuators_baseline,
                surrogate_predicted=None,
                simulated_tuned=None,
                simulated_baseline=base_dict,
                energy_baseline_kwh=float(res_baseline.energy_kwh),
                energy_tuned_kwh=None,
                energy_reduction_kwh=None,
                energy_reduction_pct=None,
                tensile_prediction_error=None,
                shrinkage_prediction_error=None,
                realized_in_spec=False,
                tensile_spec_met=False,
                shrinkage_spec_met=False,
                matched_noise_seed=seed if add_noise else None
            )

        # 3. Recommendation is feasible -> evaluate in true simulator with matched noise
        actuators_tuned = {
            "melt_temp_c": recommendation.melt_temp_c,
            "injection_pressure_mpa": recommendation.injection_pressure_mpa,
            "cooling_time_s": recommendation.cooling_time_s
        }

        rng_tuned = np.random.default_rng(seed) if (add_noise and seed is not None) else None
        res_tuned = self.simulator.evaluate_single(
            moisture_pct=moisture_pct,
            melt_flow_index=melt_flow_index,
            ambient_temp_c=ambient_temp_c,
            recycled_pct=recycled_pct,
            melt_temp_c=actuators_tuned["melt_temp_c"],
            injection_pressure_mpa=actuators_tuned["injection_pressure_mpa"],
            cooling_time_s=actuators_tuned["cooling_time_s"],
            add_noise=add_noise,
            rng=rng_tuned
        )
        tuned_dict = res_tuned.to_dict()

        # Surrogate predictions
        surr_dict = {
            "tensile_strength_mpa": recommendation.predicted_tensile_mpa,
            "volumetric_shrinkage_pct": recommendation.predicted_shrinkage_pct,
            "energy_kwh": recommendation.predicted_energy_kwh,
            "predicted_in_spec": recommendation.predicted_in_spec
        }

        # Quality errors
        t_err = (
            abs(recommendation.predicted_tensile_mpa - res_tuned.tensile_strength_mpa)
            if not np.isnan(recommendation.predicted_tensile_mpa) else None
        )
        s_err = (
            abs(recommendation.predicted_shrinkage_pct - res_tuned.volumetric_shrinkage_pct)
            if not np.isnan(recommendation.predicted_shrinkage_pct) else None
        )

        # Energy comparison
        e_base = float(res_baseline.energy_kwh)
        e_tuned = float(res_tuned.energy_kwh)
        e_saved = e_base - e_tuned
        e_pct = (e_saved / e_base) * 100.0 if e_base > 0 else 0.0

        realized_in_spec = bool(res_tuned.in_spec_flag == 1)
        tens_met = bool(res_tuned.tensile_in_spec == 1)
        shrink_met = bool(res_tuned.shrinkage_in_spec == 1)

        return SimulatorValidationResult(
            is_feasible=True,
            status=recommendation.status,
            message="Recommendation verified against authoritative simulator.",
            material_inputs=material_inputs,
            actuators_tuned=actuators_tuned,
            actuators_baseline=actuators_baseline,
            surrogate_predicted=surr_dict,
            simulated_tuned=tuned_dict,
            simulated_baseline=base_dict,
            energy_baseline_kwh=e_base,
            energy_tuned_kwh=e_tuned,
            energy_reduction_kwh=e_saved,
            energy_reduction_pct=e_pct,
            tensile_prediction_error=t_err,
            shrinkage_prediction_error=s_err,
            realized_in_spec=realized_in_spec,
            tensile_spec_met=tens_met,
            shrinkage_spec_met=shrink_met,
            matched_noise_seed=seed if add_noise else None
        )
