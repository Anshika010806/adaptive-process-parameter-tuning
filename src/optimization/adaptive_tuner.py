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
    status: str  # 'OPTIMAL', 'SUBOPTIMAL', 'INFEASIBLE', 'FALLBACK'
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AdaptiveProcessTuner:
    """
    Closed-loop adaptive process parameter controller.

    Compensates for incoming recycled material disturbances (moisture, MFI, ambient temp,
    recycled blend ratio) by dynamically adjusting machine actuators (melt temp,
    injection pressure, cooling time) to maintain quality specs while minimizing energy.

    Key Architectural Guardrails:
    1. Bounded Optimization: Actuator setpoints are strictly bounded within documented machine limits.
    2. Vectorized Multi-Start Search: Uses dense 3D candidate evaluation suitable for
       non-smooth, piece-wise constant tree-based surrogates without gradient failure.
    3. Domain Boundary Defense & Infeasibility Detection: Rejects unphysical or extreme extrapolation
       regimes where nominal targets are physically unreachable, returning safe fallback recipes.
    4. Causal Guardrail: Explicitly treats predictions as surrogate approximations, requiring
       independent physical evaluation before claiming realized manufacturing improvement.
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
        random_state: int = 42
    ):
        self.surrogate = surrogate_pipeline
        self.random_state = random_state

        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, "config", "simulation_config.json")

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = self._default_config()

        self._load_config()
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
        Precompute a dense, space-filling 3D actuator candidate grid.
        Grid points: 7 levels of T, 7 levels of P, 5 levels of cooling = 245 candidate recipes.
        """
        t_vals = np.linspace(self.bounds["melt_temp_c"][0], self.bounds["melt_temp_c"][1], 7)
        p_vals = np.linspace(self.bounds["injection_pressure_mpa"][0], self.bounds["injection_pressure_mpa"][1], 7)
        c_vals = np.linspace(self.bounds["cooling_time_s"][0], self.bounds["cooling_time_s"][1], 5)

        grid_T, grid_P, grid_C = np.meshgrid(t_vals, p_vals, c_vals, indexing="ij")
        self.candidate_actuators = np.column_stack([grid_T.ravel(), grid_P.ravel(), grid_C.ravel()])
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
        Domain boundary defense: check if material condition is physically compensable.
        """
        if moisture_pct < 0.0 or melt_flow_index <= 0.0 or recycled_pct < 0.0:
            return False, "Material parameters violate non-negativity physical bounds."

        # Extreme moisture causes irreversible voiding beyond machine actuator authority
        if moisture_pct > 0.55:
            return False, f"Extremely high moisture ({moisture_pct:.3f} wt% > 0.55 wt%) causes severe voiding that cannot be compensated within machine limits."

        # Combined severe degradation (high moisture + high recycled content)
        if moisture_pct > 0.45 and recycled_pct > 38.0:
            return False, f"Combined high moisture ({moisture_pct:.2f}%) and high recycled content ({recycled_pct:.1f}%) exceeds compensable operating envelope."

        return True, "Material condition within compensable envelope."

    def optimize_cycle(
        self,
        moisture_pct: float,
        melt_flow_index: float,
        ambient_temp_c: float,
        recycled_pct: float
    ) -> TuningRecommendation:
        """Find optimal actuator setpoints for a single manufacturing cycle."""
        is_feasible, reason = self.check_feasibility(
            moisture_pct, melt_flow_index, ambient_temp_c, recycled_pct
        )

        if not is_feasible:
            # Safe SOP fallback when target is strictly uncompensable
            sop_u = np.array([
                self.sop_defaults["melt_temp_c"],
                self.sop_defaults["injection_pressure_mpa"],
                self.sop_defaults["cooling_time_s"]
            ])
            x_mat = np.array([moisture_pct, melt_flow_index, ambient_temp_c, recycled_pct])
            pred = self.surrogate.predict(np.concatenate([x_mat, sop_u]).reshape(1, -1))[0]
            pred_E = float(self.compute_energy(sop_u[0], sop_u[1], sop_u[2], ambient_temp_c))

            return TuningRecommendation(
                melt_temp_c=sop_u[0],
                injection_pressure_mpa=sop_u[1],
                cooling_time_s=sop_u[2],
                predicted_tensile_mpa=float(pred[0]),
                predicted_shrinkage_pct=float(pred[1]),
                predicted_energy_kwh=pred_E,
                predicted_in_spec=False,
                is_feasible=False,
                status="INFEASIBLE",
                message=reason
            )

        x_mat = np.array([moisture_pct, melt_flow_index, ambient_temp_c, recycled_pct])
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

        # Multi-objective loss evaluation
        loss_S_target = ((S_preds - self.target_S) / self.tol_S) ** 2
        loss_V_target = ((V_preds - self.target_V) / self.tol_V) ** 2
        loss_E = E_preds / self.energy_norm

        viol_S = np.maximum(0.0, self.spec_S_min - S_preds) + np.maximum(0.0, S_preds - self.spec_S_max)
        viol_V = np.maximum(0.0, self.spec_V_min - V_preds) + np.maximum(0.0, V_preds - self.spec_V_max)

        candidate_losses = (
            self.w_S * (loss_S_target + self.penalty_scale * ((viol_S / self.tol_S) ** 2)) +
            self.w_V * (loss_V_target + self.penalty_scale * ((viol_V / self.tol_V) ** 2)) +
            self.w_E * loss_E
        )

        best_idx = int(np.argmin(candidate_losses))
        best_u = self.candidate_actuators[best_idx]
        best_S = float(S_preds[best_idx])
        best_V = float(V_preds[best_idx])
        best_E = float(E_preds[best_idx])

        s_in_spec = (self.spec_S_min <= best_S <= self.spec_S_max)
        v_in_spec = (self.spec_V_min <= best_V <= self.spec_V_max)
        in_spec = (s_in_spec and v_in_spec)

        status = "OPTIMAL" if in_spec else "SUBOPTIMAL"
        msg = "Optimal in-spec setpoints determined." if in_spec else "Suboptimal setpoint: surrogate predicts minor spec violation."

        return TuningRecommendation(
            melt_temp_c=float(best_u[0]),
            injection_pressure_mpa=float(best_u[1]),
            cooling_time_s=float(best_u[2]),
            predicted_tensile_mpa=best_S,
            predicted_shrinkage_pct=best_V,
            predicted_energy_kwh=best_E,
            predicted_in_spec=in_spec,
            is_feasible=True,
            status=status,
            message=msg
        )

    def tune_batch(self, df_material: pd.DataFrame) -> pd.DataFrame:
        """
        Apply adaptive tuning across an entire batch of incoming material disturbances.
        Utilizes batched surrogate evaluations for blazing speed (e.g. 750 samples in < 1 second).
        """
        missing = [col for col in self.MATERIAL_COLS if col not in df_material.columns]
        if missing:
            raise KeyError(f"Input DataFrame missing required material columns: {missing}")

        N = len(df_material)
        mat_vals = df_material[self.MATERIAL_COLS].to_numpy(dtype=float)

        # 1. Screen feasibility
        feasibility_mask = np.ones(N, dtype=bool)
        reasons = [""] * N
        for i in range(N):
            feas, r = self.check_feasibility(
                mat_vals[i, 0], mat_vals[i, 1], mat_vals[i, 2], mat_vals[i, 3]
            )
            feasibility_mask[i] = feas
            reasons[i] = r

        # Prepare outputs
        opt_T = np.full(N, self.sop_defaults["melt_temp_c"])
        opt_P = np.full(N, self.sop_defaults["injection_pressure_mpa"])
        opt_C = np.full(N, self.sop_defaults["cooling_time_s"])
        pred_S = np.zeros(N)
        pred_V = np.zeros(N)
        pred_E = np.zeros(N)
        pred_in_spec = np.zeros(N, dtype=bool)
        status_list = ["INFEASIBLE"] * N
        msg_list = list(reasons)

        feas_indices = np.where(feasibility_mask)[0]
        n_feas = len(feas_indices)

        if n_feas > 0:
            # Build giant feature matrix: (n_feas * n_candidates, 7)
            mat_feas = mat_vals[feas_indices]  # (n_feas, 4)
            # Repeat each material row n_candidates times
            mat_repeated = np.repeat(mat_feas, self.n_candidates, axis=0)  # (n_feas * K, 4)
            # Tile candidate actuators n_feas times
            cand_tiled = np.tile(self.candidate_actuators, (n_feas, 1))     # (n_feas * K, 3)
            giant_features = np.hstack([mat_repeated, cand_tiled])

            # Single vectorized forward pass
            all_preds = self.surrogate.predict(giant_features)
            all_S = all_preds[:, 0]
            all_V = all_preds[:, 1]
            all_E = self.compute_energy(
                cand_tiled[:, 0], cand_tiled[:, 1], cand_tiled[:, 2], mat_repeated[:, 2]
            )

            # Vectorized multi-objective loss
            loss_S_target = ((all_S - self.target_S) / self.tol_S) ** 2
            loss_V_target = ((all_V - self.target_V) / self.tol_V) ** 2
            loss_E = all_E / self.energy_norm

            viol_S = np.maximum(0.0, self.spec_S_min - all_S) + np.maximum(0.0, all_S - self.spec_S_max)
            viol_V = np.maximum(0.0, self.spec_V_min - all_V) + np.maximum(0.0, all_V - self.spec_V_max)

            all_losses = (
                self.w_S * (loss_S_target + self.penalty_scale * ((viol_S / self.tol_S) ** 2)) +
                self.w_V * (loss_V_target + self.penalty_scale * ((viol_V / self.tol_V) ** 2)) +
                self.w_E * loss_E
            )

            # Reshape to (n_feas, n_candidates)
            loss_matrix = all_losses.reshape(n_feas, self.n_candidates)
            best_cand_indices = np.argmin(loss_matrix, axis=1)

            # Extract optimal results
            for row_idx, cand_idx in enumerate(best_cand_indices):
                orig_idx = feas_indices[row_idx]
                flat_idx = row_idx * self.n_candidates + cand_idx

                best_actuator = self.candidate_actuators[cand_idx]
                opt_T[orig_idx] = best_actuator[0]
                opt_P[orig_idx] = best_actuator[1]
                opt_C[orig_idx] = best_actuator[2]

                s_val = float(all_S[flat_idx])
                v_val = float(all_V[flat_idx])
                e_val = float(all_E[flat_idx])

                pred_S[orig_idx] = s_val
                pred_V[orig_idx] = v_val
                pred_E[orig_idx] = e_val

                s_ok = (self.spec_S_min <= s_val <= self.spec_S_max)
                v_ok = (self.spec_V_min <= v_val <= self.spec_V_max)
                is_in_spec = (s_ok and v_ok)
                pred_in_spec[orig_idx] = is_in_spec

                status_list[orig_idx] = "OPTIMAL" if is_in_spec else "SUBOPTIMAL"
                msg_list[orig_idx] = (
                    "Optimal in-spec setpoints determined."
                    if is_in_spec
                    else "Suboptimal setpoint: surrogate predicts minor spec violation."
                )

        # For infeasible rows, compute predicted outcomes under fallback SOP
        infeas_indices = np.where(~feasibility_mask)[0]
        if len(infeas_indices) > 0:
            for orig_idx in infeas_indices:
                x_m = mat_vals[orig_idx]
                sop_feat = np.concatenate([
                    x_m,
                    [self.sop_defaults["melt_temp_c"], self.sop_defaults["injection_pressure_mpa"], self.sop_defaults["cooling_time_s"]]
                ]).reshape(1, -1)
                pred_infeas = self.surrogate.predict(sop_feat)[0]
                pred_S[orig_idx] = float(pred_infeas[0])
                pred_V[orig_idx] = float(pred_infeas[1])
                pred_E[orig_idx] = float(self.compute_energy(
                    self.sop_defaults["melt_temp_c"],
                    self.sop_defaults["injection_pressure_mpa"],
                    self.sop_defaults["cooling_time_s"],
                    x_m[2]
                ))
                pred_in_spec[orig_idx] = False

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
