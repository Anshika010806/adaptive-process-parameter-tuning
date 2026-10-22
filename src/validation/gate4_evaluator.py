"""
Gate 4: Robustness, Sensitivity, and Ablation Evaluation Engine.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 4 - Robustness and Ablation Evaluation)

This module implements the systematic evaluation framework for Gate 4:
1. Robustness: Operating contexts and stochastic repetitions under reproducible seeds and matched noise.
2. Sensitivity: Controlled sweeps of tensile safety margin and recycled-content levels within supported ranges.
3. Ablation: Direct matched comparison of the full corrected tuner against variants without adaptive
   recycled protection, intermediate margins, zero safety margins, and static SOP baseline.
4. Trade-offs: Quantitative measurement of energy reduction, tensile and shrinkage compliance,
   overall simulator ground-truth quality compliance, latency, and variability.
5. Failure analysis: Contexts with violations, infeasible optimization, or degraded performance.
"""

from __future__ import annotations
import os
import sys
import json
import time
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats

from src.simulation.process_simulator import PolymerInjectionSimulator, SimulationResult
from src.simulation.data_generator import DataGenerator
from src.optimization.static_controller import StaticSOPController
from src.optimization.domain_guard import DomainGuard, GuardResult
from src.optimization.adaptive_tuner import AdaptiveProcessTuner, TuningRecommendation
from src.optimization.simulator_validator import SimulatorValidator, SimulatorValidationResult
from src.optimization.surrogate_loader import load_or_train_surrogate
from src.validation.evaluator import compute_confidence_interval, EvaluationRecord


@dataclass(frozen=True)
class AblationVariantConfig:
    """Configuration for an individual tuner ablation variant."""
    variant_id: str
    display_name: str
    description: str
    safety_margin_tensile: float
    safety_margin_shrinkage: float
    recycled_margin_slope: float
    recycled_margin_threshold: float
    refine_local: bool = True
    is_static_sop: bool = False


@dataclass
class Gate4SummaryResult:
    """Comprehensive Gate 4 evaluation results across all studies."""
    metadata: Dict[str, Any]
    robustness_summary: Dict[str, Any]
    sensitivity_summary: Dict[str, Any]
    ablation_summary: Dict[str, Any]
    tradeoffs_summary: Dict[str, Any]
    failure_analysis: Dict[str, Any]
    actuator_safety_verification: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Gate4Evaluator:
    """
    Authoritative Gate 4 Robustness, Sensitivity, and Ablation Evaluation Engine.
    """

    MATERIAL_COLS = ["moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct"]
    ACTUATOR_COLS = ["melt_temp_c", "injection_pressure_mpa", "cooling_time_s"]

    # Hard machine actuator physical boundaries
    ACTUATOR_BOUNDS = {
        "melt_temp_c": (205.0, 255.0),
        "injection_pressure_mpa": (65.0, 145.0),
        "cooling_time_s": (12.0, 32.0),
    }

    # Authoritative Quality Targets
    QUALITY_SPECS = {
        "tensile_strength_mpa": (49.0, 55.0),
        "volumetric_shrinkage_pct": (0.80, 1.60),
    }

    def __init__(
        self,
        surrogate_pipeline=None,
        simulator: Optional[PolymerInjectionSimulator] = None,
        config_path: Optional[str] = None,
        random_state: int = 42
    ):
        self.random_state = random_state
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config", "simulation_config.json"
        )
        self.simulator = simulator or PolymerInjectionSimulator(config_path=self.config_path)
        self.static_controller = StaticSOPController()
        self.domain_guard = DomainGuard(config_path=self.config_path, reject_ood=True)
        self.data_generator = DataGenerator(simulator=self.simulator)

        if surrogate_pipeline is not None:
            self.surrogate = surrogate_pipeline
        else:
            self.surrogate = load_or_train_surrogate(model_name="RandomForest", random_state=random_state)

        self._opt_cache: Dict[Tuple, Any] = {}

    def sample_supported_contexts(self, n: int = 50, seed: int = 42) -> pd.DataFrame:
        """
        Sample reproducible in-domain operating contexts strictly within supported bounds.
        """
        df = self.data_generator.sample_material_inputs_id(n=n, seed=seed)
        df["context_id"] = np.arange(len(df))
        return df

    def create_tuner(self, variant: AblationVariantConfig) -> Optional[AdaptiveProcessTuner]:
        """Instantiate an AdaptiveProcessTuner corresponding to an ablation variant."""
        if variant.is_static_sop:
            return None
        return AdaptiveProcessTuner(
            surrogate_pipeline=self.surrogate,
            config_path=self.config_path,
            random_state=self.random_state,
            search_strategy="grid",
            grid_resolution=(11, 11, 9),
            candidate_budget=1000,
            reject_ood=True,
            refine_local=variant.refine_local,
            safety_margin_tensile=variant.safety_margin_tensile,
            safety_margin_shrinkage=variant.safety_margin_shrinkage,
            recycled_margin_slope=variant.recycled_margin_slope,
            recycled_margin_threshold=variant.recycled_margin_threshold,
            allow_fallback_to_strict=False,
            use_chance_constraint=False
        )

    def evaluate_tuner_on_context(
        self,
        tuner: Optional[AdaptiveProcessTuner],
        m: float,
        mfi: float,
        t_amb: float,
        rec_pct: float,
        matched_seed: Optional[int],
        add_noise: bool = True,
        custom_simulator: Optional[PolymerInjectionSimulator] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single cycle: runs optimization (if adaptive) and ground-truth simulator evaluation.
        Always distinguishes optimizer prediction from simulator ground truth.
        """
        sim = custom_simulator or self.simulator

        # Check domain guard first
        guard = self.domain_guard.validate_material(m, mfi, t_amb, rec_pct)
        if not guard.is_in_support or not guard.is_valid:
            return {
                "tuner_status": guard.status,
                "tuner_feasible": False,
                "tuner_message": guard.message,
                "optimization_latency_ms": 0.0,
                "deployed_melt_temp_c": self.static_controller.melt_temp_c,
                "deployed_injection_pressure_mpa": self.static_controller.injection_pressure_mpa,
                "deployed_cooling_time_s": self.static_controller.cooling_time_s,
                "surrogate_pred_tensile_mpa": None,
                "surrogate_pred_shrinkage_pct": None,
                "surrogate_pred_energy_kwh": None,
                "surrogate_pred_in_spec": None,
                "sim_tensile_mpa": float("nan"),
                "sim_shrinkage_pct": float("nan"),
                "sim_energy_kwh": float("nan"),
                "sim_tensile_in_spec": False,
                "sim_shrinkage_in_spec": False,
                "sim_all_in_spec": False,
                "quality_violation": True,
                "false_positive_quality": False,
                "actuator_limits_respected": True,
            }

        # SOP Baseline setpoints
        base_melt = self.static_controller.melt_temp_c
        base_press = self.static_controller.injection_pressure_mpa
        base_cool = self.static_controller.cooling_time_s

        if tuner is None:
            # Static SOP baseline evaluation
            t_opt_ms = 0.0
            dep_melt, dep_press, dep_cool = base_melt, base_press, base_cool
            tuner_status = "STATIC_SOP"
            tuner_feasible = True
            tuner_msg = "Static SOP reference setpoint"
            pred_s, pred_v, pred_e, pred_in_spec = None, None, None, None
        else:
            cache_key = (id(tuner), round(m, 6), round(mfi, 6), round(t_amb, 6), round(rec_pct, 6))
            if cache_key in self._opt_cache:
                tuner_status, tuner_feasible, tuner_msg, t_opt_ms, dep_melt, dep_press, dep_cool, pred_s, pred_v, pred_e, pred_in_spec = self._opt_cache[cache_key]
            else:
                # Adaptive optimization
                t_start = time.perf_counter()
                rec = tuner.optimize_cycle(m, mfi, t_amb, rec_pct)
                t_opt_ms = (time.perf_counter() - t_start) * 1000.0

                tuner_status = rec.status
                tuner_feasible = rec.is_feasible
                tuner_msg = rec.message

                if rec.is_feasible:
                    dep_melt = rec.melt_temp_c
                    dep_press = rec.injection_pressure_mpa
                    dep_cool = rec.cooling_time_s
                    pred_s = rec.predicted_tensile_mpa
                    pred_v = rec.predicted_shrinkage_pct
                    pred_e = rec.predicted_energy_kwh
                    pred_in_spec = rec.predicted_in_spec
                else:
                    # Fallback to SOP on infeasibility
                    dep_melt, dep_press, dep_cool = base_melt, base_press, base_cool
                    pred_s, pred_v, pred_e, pred_in_spec = None, None, None, False

                self._opt_cache[cache_key] = (
                    tuner_status, tuner_feasible, tuner_msg, t_opt_ms,
                    dep_melt, dep_press, dep_cool, pred_s, pred_v, pred_e, pred_in_spec
                )

        # Actuator boundary compliance verification
        b = self.ACTUATOR_BOUNDS
        actuator_ok = (
            b["melt_temp_c"][0] - 1e-4 <= dep_melt <= b["melt_temp_c"][1] + 1e-4 and
            b["injection_pressure_mpa"][0] - 1e-4 <= dep_press <= b["injection_pressure_mpa"][1] + 1e-4 and
            b["cooling_time_s"][0] - 1e-4 <= dep_cool <= b["cooling_time_s"][1] + 1e-4
        )

        # Authoritative ground-truth simulator evaluation
        rng_tuned = np.random.default_rng(matched_seed) if (add_noise and matched_seed is not None) else None
        sim_res = sim.evaluate_single(
            moisture_pct=m,
            melt_flow_index=mfi,
            ambient_temp_c=t_amb,
            recycled_pct=rec_pct,
            melt_temp_c=dep_melt,
            injection_pressure_mpa=dep_press,
            cooling_time_s=dep_cool,
            add_noise=add_noise,
            rng=rng_tuned
        )

        # Baseline simulation with identical noise seed for matched-pair energy reduction
        rng_base = np.random.default_rng(matched_seed) if (add_noise and matched_seed is not None) else None
        sim_base = sim.evaluate_single(
            moisture_pct=m,
            melt_flow_index=mfi,
            ambient_temp_c=t_amb,
            recycled_pct=rec_pct,
            melt_temp_c=base_melt,
            injection_pressure_mpa=base_press,
            cooling_time_s=base_cool,
            add_noise=add_noise,
            rng=rng_base
        )

        energy_red_kwh = sim_base.energy_kwh - sim_res.energy_kwh
        energy_red_pct = (energy_red_kwh / sim_base.energy_kwh * 100.0) if sim_base.energy_kwh > 0 else 0.0

        # Physical specification compliance
        spec_s = self.QUALITY_SPECS["tensile_strength_mpa"]
        spec_v = self.QUALITY_SPECS["volumetric_shrinkage_pct"]
        tensile_in_spec = bool(spec_s[0] <= sim_res.tensile_strength_mpa <= spec_s[1])
        shrinkage_in_spec = bool(spec_v[0] <= sim_res.volumetric_shrinkage_pct <= spec_v[1])
        all_in_spec = bool(tensile_in_spec and shrinkage_in_spec)
        quality_violation = not all_in_spec

        # False positive: optimizer predicted in-spec, but physical simulator was out of spec
        false_positive = bool(pred_in_spec is True and not all_in_spec)

        return {
            "tuner_status": tuner_status,
            "tuner_feasible": tuner_feasible,
            "tuner_message": tuner_msg,
            "optimization_latency_ms": t_opt_ms,
            "deployed_melt_temp_c": dep_melt,
            "deployed_injection_pressure_mpa": dep_press,
            "deployed_cooling_time_s": dep_cool,
            "actuator_limits_respected": actuator_ok,
            "surrogate_pred_tensile_mpa": pred_s,
            "surrogate_pred_shrinkage_pct": pred_v,
            "surrogate_pred_energy_kwh": pred_e,
            "surrogate_pred_in_spec": pred_in_spec,
            "sim_baseline_energy_kwh": sim_base.energy_kwh,
            "sim_baseline_tensile_mpa": sim_base.tensile_strength_mpa,
            "sim_baseline_shrinkage_pct": sim_base.volumetric_shrinkage_pct,
            "sim_baseline_all_in_spec": sim_base.in_spec_flag,
            "sim_tensile_mpa": sim_res.tensile_strength_mpa,
            "sim_shrinkage_pct": sim_res.volumetric_shrinkage_pct,
            "sim_energy_kwh": sim_res.energy_kwh,
            "sim_tensile_in_spec": tensile_in_spec,
            "sim_shrinkage_in_spec": shrinkage_in_spec,
            "sim_all_in_spec": all_in_spec,
            "energy_reduction_kwh": energy_red_kwh,
            "energy_reduction_pct": energy_red_pct,
            "quality_violation": quality_violation,
            "false_positive_quality": false_positive,
            "tensile_prediction_error": (pred_s - sim_res.tensile_strength_mpa) if pred_s is not None else None,
            "shrinkage_prediction_error": (pred_v - sim_res.volumetric_shrinkage_pct) if pred_v is not None else None,
        }

    # =========================================================================
    # 1. ROBUSTNESS EXPERIMENT
    # =========================================================================

    def run_robustness_experiment(
        self,
        contexts_df: pd.DataFrame,
        repetitions: int = 5,
        base_seed: int = 42,
        alternate_seeds: List[int] = [42, 1337, 2026],
        noise_levels: List[float] = [0.0, 0.35, 0.50]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Evaluate full corrected tuner robustness across:
        - Multiple operating contexts (N=contexts_df rows)
        - Stochastic repetitions with reproducible matched seeds
        - Cross-seed reproducibility across multiple base seeds
        - Matched process noise policy variations (zero noise, nominal 0.35 MPa, elevated 0.50 MPa)
        """
        variant = AblationVariantConfig(
            variant_id="full_corrected",
            display_name="Full Corrected Tuner",
            description="Base margin 1.50 MPa + adaptive recycled slope 0.035 MPa/% (>25%)",
            safety_margin_tensile=1.50,
            safety_margin_shrinkage=0.05,
            recycled_margin_slope=0.035,
            recycled_margin_threshold=25.0,
            refine_local=True
        )
        tuner = self.create_tuner(variant)

        records: List[Dict[str, Any]] = []

        # Part 1: Matched Noise Evaluation across contexts and repetitions
        for noise_sigma in noise_levels:
            # Build custom simulator with specific noise_sigma if different from default
            if abs(noise_sigma - 0.35) > 1e-4:
                # Deep copy config and modify noise_sigma
                sim_cfg = dict(self.simulator.config)
                sim_cfg["physical_coefficients"] = dict(self.simulator.config["physical_coefficients"])
                sim_cfg["physical_coefficients"]["tensile"] = dict(self.simulator.config["physical_coefficients"]["tensile"])
                sim_cfg["physical_coefficients"]["tensile"]["noise_sigma"] = noise_sigma
                sim_custom = PolymerInjectionSimulator()
                sim_custom.config = sim_cfg
                sim_custom._load_parameters()
            else:
                sim_custom = self.simulator

            add_noise = (noise_sigma > 0.0)

            for ctx_idx in range(len(contexts_df)):
                row = contexts_df.iloc[ctx_idx]
                m = float(row["moisture_pct"])
                mfi = float(row["melt_flow_index"])
                t_amb = float(row["ambient_temp_c"])
                rec_pct = float(row["recycled_pct"])

                for rep_idx in range(repetitions):
                    matched_seed = (base_seed + (ctx_idx * 1000) + rep_idx) if add_noise else None
                    cycle_res = self.evaluate_tuner_on_context(
                        tuner=tuner,
                        m=m, mfi=mfi, t_amb=t_amb, rec_pct=rec_pct,
                        matched_seed=matched_seed,
                        add_noise=add_noise,
                        custom_simulator=sim_custom
                    )
                    records.append({
                        "experiment": "noise_robustness",
                        "noise_sigma": noise_sigma,
                        "base_seed": base_seed,
                        "context_id": int(row.get("context_id", ctx_idx)),
                        "repetition_id": rep_idx,
                        "matched_seed": matched_seed,
                        "moisture_pct": m,
                        "melt_flow_index": mfi,
                        "ambient_temp_c": t_amb,
                        "recycled_pct": rec_pct,
                        **cycle_res
                    })

        # Part 2: Seed Stability Check across alternate seeds (using nominal noise)
        for seed_val in alternate_seeds:
            if seed_val == base_seed:
                continue  # already covered above
            for ctx_idx in range(len(contexts_df)):
                row = contexts_df.iloc[ctx_idx]
                m = float(row["moisture_pct"])
                mfi = float(row["melt_flow_index"])
                t_amb = float(row["ambient_temp_c"])
                rec_pct = float(row["recycled_pct"])

                for rep_idx in range(repetitions):
                    matched_seed = seed_val + (ctx_idx * 1000) + rep_idx
                    cycle_res = self.evaluate_tuner_on_context(
                        tuner=tuner,
                        m=m, mfi=mfi, t_amb=t_amb, rec_pct=rec_pct,
                        matched_seed=matched_seed,
                        add_noise=True,
                        custom_simulator=self.simulator
                    )
                    records.append({
                        "experiment": "seed_stability",
                        "noise_sigma": 0.35,
                        "base_seed": seed_val,
                        "context_id": int(row.get("context_id", ctx_idx)),
                        "repetition_id": rep_idx,
                        "matched_seed": matched_seed,
                        "moisture_pct": m,
                        "melt_flow_index": mfi,
                        "ambient_temp_c": t_amb,
                        "recycled_pct": rec_pct,
                        **cycle_res
                    })

        df_raw = pd.DataFrame(records)

        # Aggregate summary by noise level
        summary_by_noise = {}
        for noise_sigma in noise_levels:
            sub = df_raw[(df_raw["experiment"] == "noise_robustness") & (df_raw["noise_sigma"] == noise_sigma)]
            n_evals = len(sub)
            feaspct = float((sub["tuner_feasible"].sum() / n_evals) * 100.0) if n_evals else 0.0
            tensile_comp = float((sub["sim_tensile_in_spec"].sum() / n_evals) * 100.0) if n_evals else 0.0
            shrink_comp = float((sub["sim_shrinkage_in_spec"].sum() / n_evals) * 100.0) if n_evals else 0.0
            overall_comp = float((sub["sim_all_in_spec"].sum() / n_evals) * 100.0) if n_evals else 0.0
            violations = int(sub["quality_violation"].sum())
            energy_red_ci = compute_confidence_interval(sub["energy_reduction_pct"].dropna())
            summary_by_noise[f"sigma_{noise_sigma}"] = {
                "noise_sigma": noise_sigma,
                "cycles_evaluated": n_evals,
                "feasible_pct": feaspct,
                "tensile_compliance_pct": tensile_comp,
                "shrinkage_compliance_pct": shrink_comp,
                "overall_compliance_pct": overall_comp,
                "quality_violations_count": violations,
                "energy_reduction_pct": energy_red_ci,
                "mean_sim_tensile_mpa": float(sub["sim_tensile_mpa"].mean()),
                "min_sim_tensile_mpa": float(sub["sim_tensile_mpa"].min()),
            }

        # Aggregate summary across seeds
        summary_by_seed = {}
        for s in alternate_seeds:
            if s == base_seed:
                sub = df_raw[(df_raw["experiment"] == "noise_robustness") & (df_raw["noise_sigma"] == 0.35) & (df_raw["base_seed"] == s)]
            else:
                sub = df_raw[(df_raw["experiment"] == "seed_stability") & (df_raw["base_seed"] == s)]
            n_evals = len(sub)
            summary_by_seed[f"seed_{s}"] = {
                "base_seed": s,
                "cycles_evaluated": n_evals,
                "overall_compliance_pct": float((sub["sim_all_in_spec"].sum() / n_evals) * 100.0) if n_evals else 0.0,
                "energy_reduction_pct_mean": float(sub["energy_reduction_pct"].mean()),
                "energy_reduction_pct_std": float(sub["energy_reduction_pct"].std()),
                "quality_violations_count": int(sub["quality_violation"].sum()),
            }

        robustness_summary = {
            "noise_level_evaluations": summary_by_noise,
            "seed_stability_evaluations": summary_by_seed,
            "total_cycles": len(df_raw)
        }

        return df_raw, robustness_summary

    # =========================================================================
    # 2. SENSITIVITY EXPERIMENT
    # =========================================================================

    def run_sensitivity_experiment(
        self,
        contexts_df: pd.DataFrame,
        margin_levels: List[float] = [0.0, 0.40, 0.80, 1.20, 1.50, 1.80, 2.20],
        recycled_levels: List[float] = [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0],
        repetitions: int = 5,
        base_seed: int = 42
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Evaluate sensitivity within supported ranges:
        1. Tensile Safety Margin Sweep: Delta_S in [0.0, 2.20] MPa across contexts
        2. Recycled Content Sweep: C_rec in [10.0, 40.0] wt% across supported levels
        """
        records: List[Dict[str, Any]] = []

        # Part 1: Margin Sweep on representative contexts
        for margin in margin_levels:
            variant = AblationVariantConfig(
                variant_id=f"margin_{margin:.2f}",
                display_name=f"Margin {margin:.2f} MPa",
                description=f"Tensile margin {margin:.2f} MPa (fixed, no adaptive slope)",
                safety_margin_tensile=margin,
                safety_margin_shrinkage=0.05,
                recycled_margin_slope=0.0,
                recycled_margin_threshold=25.0,
                refine_local=True
            )
            tuner = self.create_tuner(variant)

            for ctx_idx in range(len(contexts_df)):
                row = contexts_df.iloc[ctx_idx]
                m = float(row["moisture_pct"])
                mfi = float(row["melt_flow_index"])
                t_amb = float(row["ambient_temp_c"])
                rec_pct = float(row["recycled_pct"])

                for rep_idx in range(repetitions):
                    matched_seed = base_seed + (ctx_idx * 1000) + rep_idx
                    cycle_res = self.evaluate_tuner_on_context(
                        tuner=tuner,
                        m=m, mfi=mfi, t_amb=t_amb, rec_pct=rec_pct,
                        matched_seed=matched_seed,
                        add_noise=True
                    )
                    records.append({
                        "sensitivity_type": "tensile_margin",
                        "sweep_param_name": "safety_margin_tensile",
                        "sweep_param_value": margin,
                        "recycled_pct_tested": rec_pct,
                        "context_id": int(row.get("context_id", ctx_idx)),
                        "repetition_id": rep_idx,
                        "matched_seed": matched_seed,
                        **cycle_res
                    })

        # Part 2: Recycled Content Sweep within supported [10.0, 40.0] wt%
        # Compare Full Corrected Tuner vs Fixed Margin (1.50 MPa) vs Unpadded (0.0 MPa)
        recycled_test_configs = [
            ("full_corrected", "Full Corrected (Adaptive Slope)", 1.50, 0.035),
            ("fixed_150", "Fixed Margin 1.50 MPa (No Slope)", 1.50, 0.0),
            ("unpadded_000", "Unpadded Margin 0.0 MPa", 0.0, 0.0),
        ]

        # Use nominal operating material baseline for moisture, MFI, ambient temp
        m_nominal = 0.15
        mfi_nominal = 22.0
        t_amb_nominal = 24.0

        for cfg_id, cfg_label, m_base, m_slope in recycled_test_configs:
            var = AblationVariantConfig(
                variant_id=cfg_id,
                display_name=cfg_label,
                description="",
                safety_margin_tensile=m_base,
                safety_margin_shrinkage=0.05 if m_base > 0 else 0.0,
                recycled_margin_slope=m_slope,
                recycled_margin_threshold=25.0,
                refine_local=True
            )
            tuner = self.create_tuner(var)

            for rec_val in recycled_levels:
                for rep_idx in range(repetitions * 2):  # 10 repetitions per level for statistical power
                    matched_seed = base_seed + int(rec_val * 100) + rep_idx
                    cycle_res = self.evaluate_tuner_on_context(
                        tuner=tuner,
                        m=m_nominal, mfi=mfi_nominal, t_amb=t_amb_nominal, rec_pct=rec_val,
                        matched_seed=matched_seed,
                        add_noise=True
                    )
                    records.append({
                        "sensitivity_type": "recycled_content",
                        "sweep_param_name": "recycled_pct",
                        "sweep_param_value": rec_val,
                        "config_variant": cfg_id,
                        "config_label": cfg_label,
                        "context_id": -1,
                        "repetition_id": rep_idx,
                        "matched_seed": matched_seed,
                        **cycle_res
                    })

        df_raw = pd.DataFrame(records)

        # Summaries
        margin_summary = {}
        for margin in margin_levels:
            sub = df_raw[(df_raw["sensitivity_type"] == "tensile_margin") & (df_raw["sweep_param_value"] == margin)]
            n_evals = len(sub)
            margin_summary[f"{margin:.2f}_mpa"] = {
                "margin_mpa": margin,
                "cycles": n_evals,
                "tensile_compliance_pct": float((sub["sim_tensile_in_spec"].sum() / n_evals) * 100.0) if n_evals else 0.0,
                "shrinkage_compliance_pct": float((sub["sim_shrinkage_in_spec"].sum() / n_evals) * 100.0) if n_evals else 0.0,
                "overall_compliance_pct": float((sub["sim_all_in_spec"].sum() / n_evals) * 100.0) if n_evals else 0.0,
                "quality_violations": int(sub["quality_violation"].sum()),
                "energy_reduction_pct_mean": float(sub["energy_reduction_pct"].mean()),
                "energy_reduction_pct_ci": compute_confidence_interval(sub["energy_reduction_pct"].dropna()),
                "mean_sim_tensile_mpa": float(sub["sim_tensile_mpa"].mean()),
                "min_sim_tensile_mpa": float(sub["sim_tensile_mpa"].min()),
            }

        recycled_summary = {}
        for rec_val in recycled_levels:
            rec_entry = {}
            for cfg_id, cfg_label, _, _ in recycled_test_configs:
                sub = df_raw[
                    (df_raw["sensitivity_type"] == "recycled_content") &
                    (df_raw["sweep_param_value"] == rec_val) &
                    (df_raw["config_variant"] == cfg_id)
                ]
                n_evals = len(sub)
                rec_entry[cfg_id] = {
                    "cycles": n_evals,
                    "overall_compliance_pct": float((sub["sim_all_in_spec"].sum() / n_evals) * 100.0) if n_evals else 0.0,
                    "violations": int(sub["quality_violation"].sum()),
                    "energy_reduction_pct_mean": float(sub["energy_reduction_pct"].mean()),
                    "mean_sim_tensile_mpa": float(sub["sim_tensile_mpa"].mean()),
                    "min_sim_tensile_mpa": float(sub["sim_tensile_mpa"].min()),
                }
            recycled_summary[f"{rec_val:.1f}_wt_pct"] = rec_entry

        sensitivity_summary = {
            "tensile_margin_sweep": margin_summary,
            "recycled_content_sweep": recycled_summary,
            "total_cycles": len(df_raw)
        }

        return df_raw, sensitivity_summary

    # =========================================================================
    # 3. ABLATION EXPERIMENT
    # =========================================================================

    def run_ablation_experiment(
        self,
        contexts_df: pd.DataFrame,
        repetitions: int = 5,
        base_seed: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Execute matched ablation study comparing:
        1. Full Corrected Tuner (Base 1.50 MPa + Adaptive Recycled Slope 0.035 MPa/%)
        2. Ablation A: Without Adaptive Recycled-Content Protection (Slope = 0.0)
        3. Ablation B: Gate 3 Initial Baseline Margin (Delta_S = 0.80 MPa, Slope = 0.0)
        4. Ablation C: Intermediate Candidate Margin (Delta_S = 1.20 MPa, Slope = 0.0)
        5. Ablation D: Without Additional Safety Margin / Unpadded (Delta_S = 0.0 MPa, Slope = 0.0)
        6. Reference: Static SOP Baseline Controller

        All variants evaluated under strictly matched contexts, repetitions, seeds, and noise realizations.
        Actuator bounds are never weakened.
        """
        variants = [
            AblationVariantConfig(
                variant_id="full_corrected",
                display_name="Full Corrected Tuner",
                description="Base margin 1.50 MPa + adaptive slope 0.035 MPa/% (>25% recycled)",
                safety_margin_tensile=1.50,
                safety_margin_shrinkage=0.05,
                recycled_margin_slope=0.035,
                recycled_margin_threshold=25.0,
                refine_local=True
            ),
            AblationVariantConfig(
                variant_id="no_recycled_protection",
                display_name="Ablation A: No Recycled Protection",
                description="Fixed margin 1.50 MPa without adaptive recycled slope (slope=0.0)",
                safety_margin_tensile=1.50,
                safety_margin_shrinkage=0.05,
                recycled_margin_slope=0.0,
                recycled_margin_threshold=25.0,
                refine_local=True
            ),
            AblationVariantConfig(
                variant_id="initial_baseline_margin",
                display_name="Ablation B: Initial Baseline Margin (0.80 MPa)",
                description="Gate 3 initial margin 0.80 MPa (slope=0.0)",
                safety_margin_tensile=0.80,
                safety_margin_shrinkage=0.05,
                recycled_margin_slope=0.0,
                recycled_margin_threshold=25.0,
                refine_local=True
            ),
            AblationVariantConfig(
                variant_id="candidate_margin_120",
                display_name="Ablation C: Candidate Margin (1.20 MPa)",
                description="Intermediate candidate margin 1.20 MPa (slope=0.0)",
                safety_margin_tensile=1.20,
                safety_margin_shrinkage=0.05,
                recycled_margin_slope=0.0,
                recycled_margin_threshold=25.0,
                refine_local=True
            ),
            AblationVariantConfig(
                variant_id="unpadded_zero_margin",
                display_name="Ablation D: Unpadded (0.00 MPa Margin)",
                description="Zero additional margin; raw spec limits (hard actuator limits strictly preserved)",
                safety_margin_tensile=0.00,
                safety_margin_shrinkage=0.00,
                recycled_margin_slope=0.0,
                recycled_margin_threshold=25.0,
                refine_local=True
            ),
            AblationVariantConfig(
                variant_id="static_sop",
                display_name="Reference: Static SOP Baseline",
                description="Fixed standard operating parameters (T=230C, P=100MPa, t=20s)",
                safety_margin_tensile=0.0,
                safety_margin_shrinkage=0.0,
                recycled_margin_slope=0.0,
                recycled_margin_threshold=25.0,
                refine_local=False,
                is_static_sop=True
            ),
        ]

        raw_records: List[Dict[str, Any]] = []
        summary_rows: List[Dict[str, Any]] = []

        n_contexts = len(contexts_df)

        for var in variants:
            tuner = self.create_tuner(var)
            var_records: List[Dict[str, Any]] = []

            for ctx_idx in range(n_contexts):
                row = contexts_df.iloc[ctx_idx]
                m = float(row["moisture_pct"])
                mfi = float(row["melt_flow_index"])
                t_amb = float(row["ambient_temp_c"])
                rec_pct = float(row["recycled_pct"])

                for rep_idx in range(repetitions):
                    matched_seed = base_seed + (ctx_idx * 1000) + rep_idx
                    cycle_res = self.evaluate_tuner_on_context(
                        tuner=tuner,
                        m=m, mfi=mfi, t_amb=t_amb, rec_pct=rec_pct,
                        matched_seed=matched_seed,
                        add_noise=True
                    )
                    entry = {
                        "variant_id": var.variant_id,
                        "variant_name": var.display_name,
                        "context_id": int(row.get("context_id", ctx_idx)),
                        "repetition_id": rep_idx,
                        "matched_seed": matched_seed,
                        "moisture_pct": m,
                        "melt_flow_index": mfi,
                        "ambient_temp_c": t_amb,
                        "recycled_pct": rec_pct,
                        **cycle_res
                    }
                    var_records.append(entry)
                    raw_records.append(entry)

            df_var = pd.DataFrame(var_records)
            n_evals = len(df_var)

            # Metrics
            feas_pct = float((df_var["tuner_feasible"].sum() / n_evals) * 100.0)
            tensile_comp = float((df_var["sim_tensile_in_spec"].sum() / n_evals) * 100.0)
            shrink_comp = float((df_var["sim_shrinkage_in_spec"].sum() / n_evals) * 100.0)
            overall_comp = float((df_var["sim_all_in_spec"].sum() / n_evals) * 100.0)
            total_violations = int(df_var["quality_violation"].sum())
            false_positives = int(df_var["false_positive_quality"].sum())
            actuator_safe = bool(df_var["actuator_limits_respected"].all())

            # Energy metrics
            mean_energy = float(df_var["sim_energy_kwh"].mean())
            std_energy = float(df_var["sim_energy_kwh"].std())
            energy_red_ci = compute_confidence_interval(df_var["energy_reduction_pct"].dropna())

            # Latency metrics
            lat_mean = float(df_var["optimization_latency_ms"].mean())
            lat_median = float(df_var["optimization_latency_ms"].median())
            lat_p95 = float(np.percentile(df_var["optimization_latency_ms"], 95))

            summary_rows.append({
                "variant_id": var.variant_id,
                "variant_name": var.display_name,
                "total_cycles": n_evals,
                "optimizer_feasible_pct": feas_pct,
                "tensile_compliance_pct": tensile_comp,
                "shrinkage_compliance_pct": shrink_comp,
                "overall_quality_compliance_pct": overall_comp,
                "total_defects": total_violations,
                "false_positive_count": false_positives,
                "mean_energy_kwh": mean_energy,
                "std_energy_kwh": std_energy,
                "energy_reduction_pct_mean": energy_red_ci["mean"],
                "energy_reduction_pct_ci_lower": energy_red_ci["ci_lower"],
                "energy_reduction_pct_ci_upper": energy_red_ci["ci_upper"],
                "energy_reduction_pct_std": energy_red_ci["std"],
                "mean_sim_tensile_mpa": float(df_var["sim_tensile_mpa"].mean()),
                "min_sim_tensile_mpa": float(df_var["sim_tensile_mpa"].min()),
                "mean_sim_shrinkage_pct": float(df_var["sim_shrinkage_pct"].mean()),
                "latency_mean_ms": lat_mean,
                "latency_p95_ms": lat_p95,
                "actuator_limits_strictly_respected": actuator_safe,
            })

        df_raw = pd.DataFrame(raw_records)
        df_summary = pd.DataFrame(summary_rows)

        ablation_dict = {
            "variants_evaluated": summary_rows,
            "total_cycles": len(df_raw),
            "contexts_count": n_contexts,
            "repetitions_count": repetitions
        }

        return df_raw, df_summary, ablation_dict

    # =========================================================================
    # 4. TRADE-OFFS & FAILURE ANALYSIS
    # =========================================================================

    def analyze_failures_and_tradeoffs(
        self,
        df_ablation_raw: pd.DataFrame,
        df_ablation_summary: pd.DataFrame
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Analyze multi-objective trade-offs and detailed failure distributions.
        """
        # Trade-offs analysis
        tradeoffs = []
        for _, row in df_ablation_summary.iterrows():
            tradeoffs.append({
                "variant_id": row["variant_id"],
                "variant_name": row["variant_name"],
                "energy_reduction_pct": row["energy_reduction_pct_mean"],
                "quality_compliance_pct": row["overall_quality_compliance_pct"],
                "defect_count": int(row["total_defects"]),
                "false_positive_count": int(row["false_positive_count"]),
                "runtime_mean_ms": row["latency_mean_ms"],
                "runtime_p95_ms": row["latency_p95_ms"],
                "energy_variability_std_kwh": row["std_energy_kwh"],
                "tensile_margin_over_spec_min": row["min_sim_tensile_mpa"] - 49.0
            })

        # Failure distribution by recycled content quartile across all variants
        # Quartile boundaries: Q1 (10-17.5), Q2 (17.5-25), Q3 (25-32.5), Q4 (32.5-40)
        recycled_quartile_failures = {}
        for var_id in df_ablation_raw["variant_id"].unique():
            sub = df_ablation_raw[df_ablation_raw["variant_id"] == var_id]
            q1 = sub[sub["recycled_pct"] <= 17.5]
            q2 = sub[(sub["recycled_pct"] > 17.5) & (sub["recycled_pct"] <= 25.0)]
            q3 = sub[(sub["recycled_pct"] > 25.0) & (sub["recycled_pct"] <= 32.5)]
            q4 = sub[sub["recycled_pct"] > 32.5]

            recycled_quartile_failures[var_id] = {
                "Q1_recycled_le_17.5": {
                    "total": len(q1),
                    "violations": int(q1["quality_violation"].sum()),
                    "compliance_pct": float((q1["sim_all_in_spec"].sum() / len(q1)) * 100.0) if len(q1) else 100.0
                },
                "Q2_recycled_17.5_25.0": {
                    "total": len(q2),
                    "violations": int(q2["quality_violation"].sum()),
                    "compliance_pct": float((q2["sim_all_in_spec"].sum() / len(q2)) * 100.0) if len(q2) else 100.0
                },
                "Q3_recycled_25.0_32.5": {
                    "total": len(q3),
                    "violations": int(q3["quality_violation"].sum()),
                    "compliance_pct": float((q3["sim_all_in_spec"].sum() / len(q3)) * 100.0) if len(q3) else 100.0
                },
                "Q4_recycled_gt_32.5": {
                    "total": len(q4),
                    "violations": int(q4["quality_violation"].sum()),
                    "compliance_pct": float((q4["sim_all_in_spec"].sum() / len(q4)) * 100.0) if len(q4) else 100.0
                },
            }

        # Moisture failure breakdown
        moisture_failures = {}
        for var_id in df_ablation_raw["variant_id"].unique():
            sub = df_ablation_raw[df_ablation_raw["variant_id"] == var_id]
            m_low = sub[sub["moisture_pct"] <= 0.20]
            m_mid = sub[(sub["moisture_pct"] > 0.20) & (sub["moisture_pct"] <= 0.35)]
            m_high = sub[sub["moisture_pct"] > 0.35]

            moisture_failures[var_id] = {
                "moisture_le_0.20": {
                    "total": len(m_low),
                    "violations": int(m_low["quality_violation"].sum()),
                    "compliance_pct": float((m_low["sim_all_in_spec"].sum() / len(m_low)) * 100.0) if len(m_low) else 100.0
                },
                "moisture_0.20_0.35": {
                    "total": len(m_mid),
                    "violations": int(m_mid["quality_violation"].sum()),
                    "compliance_pct": float((m_mid["sim_all_in_spec"].sum() / len(m_mid)) * 100.0) if len(m_mid) else 100.0
                },
                "moisture_gt_0.35": {
                    "total": len(m_high),
                    "violations": int(m_high["quality_violation"].sum()),
                    "compliance_pct": float((m_high["sim_all_in_spec"].sum() / len(m_high)) * 100.0) if len(m_high) else 100.0
                },
            }

        # Actuator boundary audit
        actuator_audit = {}
        for var_id in df_ablation_raw["variant_id"].unique():
            sub = df_ablation_raw[df_ablation_raw["variant_id"] == var_id]
            actuator_audit[var_id] = {
                "all_actuators_within_hard_bounds": bool(sub["actuator_limits_respected"].all()),
                "min_melt_temp_c": float(sub["deployed_melt_temp_c"].min()),
                "max_melt_temp_c": float(sub["deployed_melt_temp_c"].max()),
                "min_injection_pressure_mpa": float(sub["deployed_injection_pressure_mpa"].min()),
                "max_injection_pressure_mpa": float(sub["deployed_injection_pressure_mpa"].max()),
                "min_cooling_time_s": float(sub["deployed_cooling_time_s"].min()),
                "max_cooling_time_s": float(sub["deployed_cooling_time_s"].max()),
            }

        failure_analysis = {
            "recycled_quartile_failures": recycled_quartile_failures,
            "moisture_failures": moisture_failures,
            "actuator_audit": actuator_audit
        }

        tradeoffs_summary = {
            "tradeoffs_matrix": tradeoffs
        }

        return tradeoffs_summary, failure_analysis
