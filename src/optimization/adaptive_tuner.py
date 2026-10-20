"""
Adaptive Process Parameter Tuner for Multi-Objective Quality Control.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 2)
"""

from __future__ import annotations
import os
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from .domain_guard import DomainGuard, GuardResult


@dataclass(frozen=True)
class TuningRecommendation:
    """Immutable recommendation produced by the adaptive parameter tuner."""
    melt_temp_c: float
    injection_pressure_mpa: float
    cooling_time_s: float
    predicted_tensile_mpa: float
    predicted_shrinkage_pct: float
    predicted_energy_kwh: float
    predicted_in_spec: bool
    is_feasible: bool
    status: str  # 'OPTIMAL', 'SUBOPTIMAL', 'INFEASIBLE', 'OOD_REJECTED', 'INVALID_INPUT'
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AdaptiveProcessTuner:
    """
    Closed-loop adaptive process parameter controller.

    Compensates for incoming recycled material disturbances (moisture, MFI, ambient temp,
    recycled blend ratio) by dynamically adjusting machine actuators (melt temp,
    injection pressure, cooling time) to maintain quality specs while minimizing energy.

    Key Architectural Guardrails (Gate 2 Specification):
    1. Domain Guard & OOD Rejection: Detects inputs outside training distribution support;
       rejects OOD conditions by default with explicit status 'OOD_REJECTED' without trusting
       unsupported surrogate predictions or silently clipping inputs.
    2. Constrained Derivative-Free Optimization: Minimizes specific energy per cycle subject
       to hard quality constraints (tensile 49-55 MPa, shrinkage 0.80-1.60%). Rejects
       quality-infeasible candidates even if energy is low.
    3. Strictly Bounded Actuators: Guarantees melt temp in [205, 255] C, injection pressure
       in [65, 145] MPa, cooling time in [12, 32] s.
    4. Causal & Simulator Decoupling: Treats predictions as surrogate estimates, leaving
       authoritative validation to the physical simulator.
    """

    FEATURE_COLS = [
        "moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct",
        "melt_temp_c", "injection_pressure_mpa", "cooling_time_s"
    ]
    MATERIAL_COLS = ["moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct"]
    ACTUATOR_COLS = ["melt_temp_c", "injection_pressure_mpa", "cooling_time_s"]

    def __init__(
        self,
        surrogate_pipeline: Pipeline,
        config_path: Optional[str] = None,
        random_state: int = 42,
        search_strategy: str = "grid",
        grid_resolution: Tuple[int, int, int] = (11, 11, 9),
        candidate_budget: int = 1000,
        reject_ood: bool = True,
        refine_local: bool = True,
        safety_margin_tensile: float = 0.80,
        safety_margin_shrinkage: float = 0.05
    ):
        self.surrogate = surrogate_pipeline
        self.random_state = random_state
        self.search_strategy = search_strategy
        self.grid_resolution = grid_resolution
        self.candidate_budget = candidate_budget
        self.reject_ood = reject_ood
        self.refine_local = refine_local
        self.safety_margin_tensile = safety_margin_tensile
        self.safety_margin_shrinkage = safety_margin_shrinkage

        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, "config", "simulation_config.json")

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = self._default_config()

        self._load_config()
        self.domain_guard = DomainGuard(config_path=config_path, reject_ood=reject_ood)
        self._precompute_candidates()

    def _default_config(self) -> Dict[str, Any]:
        """Fallback defaults matching simulation_config.json."""
        return {
            "process_parameters": {
                "melt_temp_c": {"nominal_sop": 230.0, "min_bound": 205.0, "max_bound": 255.0},
                "injection_pressure_mpa": {"nominal_sop": 100.0, "min_bound": 65.0, "max_bound": 145.0},
                "cooling_time_s": {"nominal_sop": 20.0, "min_bound": 12.0, "max_bound": 32.0}
            },
            "quality_targets": {
                "tensile_strength_mpa": {"target": 52.0, "spec_min": 49.0, "spec_max": 55.0},
                "volumetric_shrinkage_pct": {"target": 1.20, "spec_min": 0.80, "spec_max": 1.60},
                "energy_kwh": {"max_acceptable": 4.20, "nominal": 3.15}
            },
            "optimization": {
                "weights": {"tensile": 0.50, "shrinkage": 0.35, "energy": 0.15},
                "penalty_scale": 100.0
            },
            "physical_coefficients": {
                "energy": {"E_0": 0.20, "c_thermal": 0.008, "c_hydraulic": 0.009, "c_dwell": 0.030}
            }
        }

    def _load_config(self) -> None:
        """Cache bounds, weights, and energy coefficients."""
        p_cfg = self.config["process_parameters"]
        self.bounds = {
            "melt_temp_c": (float(p_cfg["melt_temp_c"]["min_bound"]), float(p_cfg["melt_temp_c"]["max_bound"])),
            "injection_pressure_mpa": (float(p_cfg["injection_pressure_mpa"]["min_bound"]), float(p_cfg["injection_pressure_mpa"]["max_bound"])),
            "cooling_time_s": (float(p_cfg["cooling_time_s"]["min_bound"]), float(p_cfg["cooling_time_s"]["max_bound"]))
        }
        self.sop_defaults = {
            "melt_temp_c": float(p_cfg["melt_temp_c"]["nominal_sop"]),
            "injection_pressure_mpa": float(p_cfg["injection_pressure_mpa"]["nominal_sop"]),
            "cooling_time_s": float(p_cfg["cooling_time_s"]["nominal_sop"])
        }

        q_cfg = self.config["quality_targets"]
        self.target_S = float(q_cfg["tensile_strength_mpa"]["target"])
        self.spec_S_min = float(q_cfg["tensile_strength_mpa"]["spec_min"])
        self.spec_S_max = float(q_cfg["tensile_strength_mpa"]["spec_max"])
        self.tol_S = (self.spec_S_max - self.spec_S_min) / 2.0  # 3.0 MPa

        self.target_V = float(q_cfg["volumetric_shrinkage_pct"]["target"])
        self.spec_V_min = float(q_cfg["volumetric_shrinkage_pct"]["spec_min"])
        self.spec_V_max = float(q_cfg["volumetric_shrinkage_pct"]["spec_max"])
        self.tol_V = (self.spec_V_max - self.spec_V_min) / 2.0  # 0.40 %

        self.energy_norm = float(q_cfg["energy_kwh"]["nominal"])  # 3.15 kWh

        opt_cfg = self.config.get("optimization", {})
        w = opt_cfg.get("weights", {"tensile": 0.50, "shrinkage": 0.35, "energy": 0.15})
        self.w_S = float(w["tensile"])
        self.w_V = float(w["shrinkage"])
        self.w_E = float(w["energy"])
        self.penalty_scale = float(opt_cfg.get("penalty_scale", 100.0))

        e_cfg = self.config["physical_coefficients"]["energy"]
        self.E_0 = float(e_cfg["E_0"])
        self.c_thermal = float(e_cfg["c_thermal"])
        self.c_hydraulic = float(e_cfg["c_hydraulic"])
        self.c_dwell = float(e_cfg["c_dwell"])

    def _precompute_candidates(self) -> None:
        """
        Precompute bounded derivative-free candidate setpoints.
        Supports dense grid or bounded stratified sampling, always anchoring nominal SOP.
        """
        nominal_sop = np.array([
            self.sop_defaults["melt_temp_c"],
            self.sop_defaults["injection_pressure_mpa"],
            self.sop_defaults["cooling_time_s"]
        ])

        if self.search_strategy in ["sampling", "random"]:
            rng = np.random.default_rng(self.random_state)
            t_samples = rng.uniform(self.bounds["melt_temp_c"][0], self.bounds["melt_temp_c"][1], self.candidate_budget)
            p_samples = rng.uniform(self.bounds["injection_pressure_mpa"][0], self.bounds["injection_pressure_mpa"][1], self.candidate_budget)
            c_samples = rng.uniform(self.bounds["cooling_time_s"][0], self.bounds["cooling_time_s"][1], self.candidate_budget)
            candidates = np.column_stack([t_samples, p_samples, c_samples])
            # Prepend nominal SOP
            self.candidate_actuators = np.vstack([nominal_sop, candidates])
        else:
            # Default: Grid (e.g. 11 x 11 x 9 = 1089 recipes)
            nT, nP, nC = self.grid_resolution
            t_vals = np.linspace(self.bounds["melt_temp_c"][0], self.bounds["melt_temp_c"][1], nT)
            p_vals = np.linspace(self.bounds["injection_pressure_mpa"][0], self.bounds["injection_pressure_mpa"][1], nP)
            c_vals = np.linspace(self.bounds["cooling_time_s"][0], self.bounds["cooling_time_s"][1], nC)

            grid_T, grid_P, grid_C = np.meshgrid(t_vals, p_vals, c_vals, indexing="ij")
            grid_candidates = np.column_stack([grid_T.ravel(), grid_P.ravel(), grid_C.ravel()])
            # Ensure nominal SOP is included exactly
            self.candidate_actuators = np.vstack([nominal_sop, grid_candidates])

        # Deduplicate and clamp strictly to actuator machine limits
        self.candidate_actuators[:, 0] = np.clip(self.candidate_actuators[:, 0], self.bounds["melt_temp_c"][0], self.bounds["melt_temp_c"][1])
        self.candidate_actuators[:, 1] = np.clip(self.candidate_actuators[:, 1], self.bounds["injection_pressure_mpa"][0], self.bounds["injection_pressure_mpa"][1])
        self.candidate_actuators[:, 2] = np.clip(self.candidate_actuators[:, 2], self.bounds["cooling_time_s"][0], self.bounds["cooling_time_s"][1])
        self.candidate_actuators = np.unique(self.candidate_actuators, axis=0)
        self.n_candidates = len(self.candidate_actuators)

    def compute_energy(
        self,
        melt_temp_c: Union[float, np.ndarray],
        injection_pressure_mpa: Union[float, np.ndarray],
        cooling_time_s: Union[float, np.ndarray],
        ambient_temp_c: Union[float, np.ndarray]
    ) -> Union[float, np.ndarray]:
        """Compute specific process energy consumption (kWh/cycle)."""
        temp_delta = np.maximum(0.0, melt_temp_c - ambient_temp_c)
        P_ref = 100.0
        return (
            self.E_0 +
            self.c_thermal * temp_delta +
            self.c_hydraulic * (injection_pressure_mpa / P_ref) +
            self.c_dwell * cooling_time_s
        )

    def check_feasibility(
        self,
        moisture_pct: float,
        melt_flow_index: float,
        ambient_temp_c: float,
        recycled_pct: float
    ) -> Tuple[bool, str]:
        """
        Check if material condition is physically compensable and in-support.
        Maintains backward compatibility with Gate 0 / Gate 1 test interfaces.
        """
        guard_res = self.domain_guard.validate_material(
            moisture_pct=moisture_pct,
            melt_flow_index=melt_flow_index,
            ambient_temp_c=ambient_temp_c,
            recycled_pct=recycled_pct
        )
        return guard_res.is_feasible, guard_res.message

    def _local_refinement(
        self,
        best_u: np.ndarray,
        x_mat: np.ndarray,
        ambient_temp_c: float
    ) -> Tuple[np.ndarray, float, float, float]:
        """
        Optional local bounded grid search around a promising candidate to fine-tune energy.
        """
        t_span = np.linspace(max(self.bounds["melt_temp_c"][0], best_u[0] - 2.5),
                             min(self.bounds["melt_temp_c"][1], best_u[0] + 2.5), 5)
        p_span = np.linspace(max(self.bounds["injection_pressure_mpa"][0], best_u[1] - 4.0),
                             min(self.bounds["injection_pressure_mpa"][1], best_u[1] + 4.0), 5)
        c_span = np.linspace(max(self.bounds["cooling_time_s"][0], best_u[2] - 1.0),
                             min(self.bounds["cooling_time_s"][1], best_u[2] + 1.0), 5)

        gT, gP, gC = np.meshgrid(t_span, p_span, c_span, indexing="ij")
        refined_cands = np.column_stack([gT.ravel(), gP.ravel(), gC.ravel()])

        n_ref = len(refined_cands)
        x_mat_rep = np.tile(x_mat, (n_ref, 1))
        ref_feats = np.hstack([x_mat_rep, refined_cands])

        ref_preds = self.surrogate.predict(ref_feats)
        ref_S = ref_preds[:, 0]
        ref_V = ref_preds[:, 1]
        ref_E = self.compute_energy(refined_cands[:, 0], refined_cands[:, 1], refined_cands[:, 2], ambient_temp_c)

        in_spec_mask = (
            (self.spec_S_min <= ref_S) & (ref_S <= self.spec_S_max) &
            (self.spec_V_min <= ref_V) & (ref_V <= self.spec_V_max)
        )

        if np.any(in_spec_mask):
            spec_indices = np.where(in_spec_mask)[0]
            best_ref_idx = spec_indices[int(np.argmin(ref_E[spec_indices]))]
            return (
                refined_cands[best_ref_idx],
                float(ref_S[best_ref_idx]),
                float(ref_V[best_ref_idx]),
                float(ref_E[best_ref_idx])
            )

        return best_u, np.nan, np.nan, np.nan

    def optimize_cycle(
        self,
        moisture_pct: float,
        melt_flow_index: float,
        ambient_temp_c: float,
        recycled_pct: float
    ) -> TuningRecommendation:
        """
        Find optimal actuator setpoints minimizing energy subject to hard quality constraints.
        """
        guard_res = self.domain_guard.validate_material(
            moisture_pct=moisture_pct,
            melt_flow_index=melt_flow_index,
            ambient_temp_c=ambient_temp_c,
            recycled_pct=recycled_pct
        )

        sop_u = np.array([
            self.sop_defaults["melt_temp_c"],
            self.sop_defaults["injection_pressure_mpa"],
            self.sop_defaults["cooling_time_s"]
        ])
        sop_E = float(self.compute_energy(sop_u[0], sop_u[1], sop_u[2], ambient_temp_c))

        # Handle non-feasible conditions (OOD, uncompensable, or invalid)
        if not guard_res.is_feasible:
            # Never trust surrogate predictions on unsupported OOD or uncompensable regimes
            return TuningRecommendation(
                melt_temp_c=float(sop_u[0]),
                injection_pressure_mpa=float(sop_u[1]),
                cooling_time_s=float(sop_u[2]),
                predicted_tensile_mpa=float("nan"),
                predicted_shrinkage_pct=float("nan"),
                predicted_energy_kwh=sop_E,
                predicted_in_spec=False,
                is_feasible=False,
                status=guard_res.status,
                message=guard_res.message
            )

        x_mat = np.array([moisture_pct, melt_flow_index, ambient_temp_c, recycled_pct], dtype=float)
        x_mat_repeated = np.tile(x_mat, (self.n_candidates, 1))
        features_batched = np.hstack([x_mat_repeated, self.candidate_actuators])

        # Vectorized batch prediction across all candidate setpoints
        preds = self.surrogate.predict(features_batched)
        S_preds = preds[:, 0]
        V_preds = preds[:, 1]
        E_preds = self.compute_energy(
            self.candidate_actuators[:, 0],
            self.candidate_actuators[:, 1],
            self.candidate_actuators[:, 2],
            ambient_temp_c
        )

        # Hard quality constraint filtering with safety margins
        s_min_safe = self.spec_S_min + self.safety_margin_tensile
        s_max_safe = self.spec_S_max - self.safety_margin_tensile
        v_min_safe = self.spec_V_min + self.safety_margin_shrinkage
        v_max_safe = self.spec_V_max - self.safety_margin_shrinkage

        feasible_safe = (
            (s_min_safe <= S_preds) & (S_preds <= s_max_safe) &
            (v_min_safe <= V_preds) & (V_preds <= v_max_safe) &
            np.isfinite(S_preds) & np.isfinite(V_preds)
        )
        feasible_strict = (
            (self.spec_S_min <= S_preds) & (S_preds <= self.spec_S_max) &
            (self.spec_V_min <= V_preds) & (V_preds <= self.spec_V_max) &
            np.isfinite(S_preds) & np.isfinite(V_preds)
        )
        feasible_mask = feasible_safe if np.any(feasible_safe) else feasible_strict

        if np.any(feasible_mask):
            feasible_indices = np.where(feasible_mask)[0]
            # Among feasible candidates, minimize energy (with mild centering tie-breaker)
            centering_penalty = 1e-4 * (
                ((S_preds[feasible_indices] - self.target_S) / self.tol_S) ** 2 +
                ((V_preds[feasible_indices] - self.target_V) / self.tol_V) ** 2
            )
            scores = E_preds[feasible_indices] + centering_penalty
            best_idx = feasible_indices[int(np.argmin(scores))]

            best_u = self.candidate_actuators[best_idx]
            best_S = float(S_preds[best_idx])
            best_V = float(V_preds[best_idx])
            best_E = float(E_preds[best_idx])

            # Optional local refinement
            if self.refine_local:
                ref_u, ref_S, ref_V, ref_E = self._local_refinement(best_u, x_mat, ambient_temp_c)
                if not np.isnan(ref_S) and ref_E < best_E:
                    best_u, best_S, best_V, best_E = ref_u, ref_S, ref_V, ref_E

            return TuningRecommendation(
                melt_temp_c=float(best_u[0]),
                injection_pressure_mpa=float(best_u[1]),
                cooling_time_s=float(best_u[2]),
                predicted_tensile_mpa=best_S,
                predicted_shrinkage_pct=best_V,
                predicted_energy_kwh=best_E,
                predicted_in_spec=True,
                is_feasible=True,
                status="OPTIMAL",
                message="Optimal in-spec setpoints determined minimizing energy."
            )

        # No candidate satisfied hard constraints -> Explicit failure status
        return TuningRecommendation(
            melt_temp_c=float(sop_u[0]),
            injection_pressure_mpa=float(sop_u[1]),
            cooling_time_s=float(sop_u[2]),
            predicted_tensile_mpa=float("nan"),
            predicted_shrinkage_pct=float("nan"),
            predicted_energy_kwh=sop_E,
            predicted_in_spec=False,
            is_feasible=False,
            status="INFEASIBLE",
            message=f"No candidate setpoint satisfies hard quality constraints (tensile: [{self.spec_S_min}, {self.spec_S_max}], shrinkage: [{self.spec_V_min}, {self.spec_V_max}])."
        )

    def tune_batch(self, df_material: pd.DataFrame) -> pd.DataFrame:
        """
        Apply adaptive tuning across an entire batch of incoming material disturbances.
        Enforces domain guard screens and vectorized candidate evaluation.
        """
        missing = [col for col in self.MATERIAL_COLS if col not in df_material.columns]
        if missing:
            raise KeyError(f"Input DataFrame missing required material columns: {missing}")

        N = len(df_material)
        mat_vals = df_material[self.MATERIAL_COLS].to_numpy(dtype=float)

        # 1. Screen domain guard
        guard_results = self.domain_guard.validate_batch(df_material)
        feasibility_mask = np.array([r.is_feasible for r in guard_results], dtype=bool)
        status_list = [r.status for r in guard_results]
        msg_list = [r.message for r in guard_results]

        # Prepare outputs initialized to fallback SOP
        opt_T = np.full(N, self.sop_defaults["melt_temp_c"], dtype=float)
        opt_P = np.full(N, self.sop_defaults["injection_pressure_mpa"], dtype=float)
        opt_C = np.full(N, self.sop_defaults["cooling_time_s"], dtype=float)
        pred_S = np.full(N, np.nan, dtype=float)
        pred_V = np.full(N, np.nan, dtype=float)
        pred_E = np.zeros(N, dtype=float)
        pred_in_spec = np.zeros(N, dtype=bool)

        for i in range(N):
            pred_E[i] = float(self.compute_energy(opt_T[i], opt_P[i], opt_C[i], mat_vals[i, 2]))

        feas_indices = np.where(feasibility_mask)[0]
        n_feas = len(feas_indices)

        if n_feas > 0:
            mat_feas = mat_vals[feas_indices]
            mat_repeated = np.repeat(mat_feas, self.n_candidates, axis=0)
            cand_tiled = np.tile(self.candidate_actuators, (n_feas, 1))
            giant_features = np.hstack([mat_repeated, cand_tiled])

            # Forward pass across candidate setpoints
            all_preds = self.surrogate.predict(giant_features)
            all_S = all_preds[:, 0]
            all_V = all_preds[:, 1]
            all_E = self.compute_energy(
                cand_tiled[:, 0], cand_tiled[:, 1], cand_tiled[:, 2], mat_repeated[:, 2]
            )

            # Reshape per batch row
            matrix_S = all_S.reshape(n_feas, self.n_candidates)
            matrix_V = all_V.reshape(n_feas, self.n_candidates)
            matrix_E = all_E.reshape(n_feas, self.n_candidates)

            for row_idx, orig_idx in enumerate(feas_indices):
                s_row = matrix_S[row_idx]
                v_row = matrix_V[row_idx]
                e_row = matrix_E[row_idx]

                s_min_safe = self.spec_S_min + self.safety_margin_tensile
                s_max_safe = self.spec_S_max - self.safety_margin_tensile
                v_min_safe = self.spec_V_min + self.safety_margin_shrinkage
                v_max_safe = self.spec_V_max - self.safety_margin_shrinkage

                in_spec_safe = (
                    (s_min_safe <= s_row) & (s_row <= s_max_safe) &
                    (v_min_safe <= v_row) & (v_row <= v_max_safe) &
                    np.isfinite(s_row) & np.isfinite(v_row)
                )
                in_spec_strict = (
                    (self.spec_S_min <= s_row) & (s_row <= self.spec_S_max) &
                    (self.spec_V_min <= v_row) & (v_row <= self.spec_V_max) &
                    np.isfinite(s_row) & np.isfinite(v_row)
                )
                in_spec = in_spec_safe if np.any(in_spec_safe) else in_spec_strict

                if np.any(in_spec):
                    spec_cand_idx = np.where(in_spec)[0]
                    centering_penalty = 1e-4 * (
                        ((s_row[spec_cand_idx] - self.target_S) / self.tol_S) ** 2 +
                        ((v_row[spec_cand_idx] - self.target_V) / self.tol_V) ** 2
                    )
                    best_cand_idx = spec_cand_idx[int(np.argmin(e_row[spec_cand_idx] + centering_penalty))]

                    best_actuator = self.candidate_actuators[best_cand_idx]
                    opt_T[orig_idx] = float(best_actuator[0])
                    opt_P[orig_idx] = float(best_actuator[1])
                    opt_C[orig_idx] = float(best_actuator[2])

                    pred_S[orig_idx] = float(s_row[best_cand_idx])
                    pred_V[orig_idx] = float(v_row[best_cand_idx])
                    pred_E[orig_idx] = float(e_row[best_cand_idx])
                    pred_in_spec[orig_idx] = True
                    status_list[orig_idx] = "OPTIMAL"
                    msg_list[orig_idx] = "Optimal in-spec setpoints determined."
                else:
                    feasibility_mask[orig_idx] = False
                    status_list[orig_idx] = "INFEASIBLE"
                    msg_list[orig_idx] = "No candidate setpoint satisfies hard quality constraints."

        res_df = pd.DataFrame({
            "melt_temp_c": opt_T,
            "injection_pressure_mpa": opt_P,
            "cooling_time_s": opt_C,
            "predicted_tensile_mpa": pred_S,
            "predicted_shrinkage_pct": pred_V,
            "predicted_energy_kwh": pred_E,
            "predicted_in_spec": pred_in_spec,
            "is_feasible": feasibility_mask,
            "status": status_list,
            "message": msg_list
        })

        return pd.concat([df_material.reset_index(drop=True), res_df], axis=1)
