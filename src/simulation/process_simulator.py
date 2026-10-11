"""
Process Simulator: Polymer Injection Molding under Recycled Feedstock Variability.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, Union, Optional
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SimulationResult:
    """Immutable result container for a single simulated manufacturing cycle."""
    tensile_strength_mpa: float
    volumetric_shrinkage_pct: float
    energy_kwh: float
    in_spec_flag: int
    tensile_in_spec: int
    shrinkage_in_spec: int
    target_infeasible_flag: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PolymerInjectionSimulator:
    """
    Phenomenological Ground-Truth Simulator for Recycled Polymer Injection Molding.

    Mathematical Model:
      y = f_true(x_mat, u) + epsilon
      where:
        x_mat = [moisture_pct, melt_flow_index, ambient_temp_c, recycled_pct]
        u     = [melt_temp_c, injection_pressure_mpa, cooling_time_s]
        y     = [tensile_strength_mpa, volumetric_shrinkage_pct, energy_kwh]

    Units & Conventions:
      - moisture_pct: Percentage by weight (wt %) in [0.05, 0.50]
      - melt_flow_index: g/10 min in [14.0, 30.0]
      - ambient_temp_c: deg C in [16.0, 32.0]
      - recycled_pct: Percentage by weight (wt %) in [10.0, 40.0]
      - melt_temp_c: deg C in [205.0, 255.0]
      - injection_pressure_mpa: MPa in [65.0, 145.0]
      - cooling_time_s: s in [12.0, 32.0]
      - tensile_strength_mpa: target 52.0 MPa (spec: [49.0, 55.0])
      - volumetric_shrinkage_pct: target 1.20 % (spec: [0.80, 1.60])
      - energy_kwh: specific energy consumption (target: minimize)
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize simulator with coefficients from configuration."""
        if config_path is None:
            # Default relative to module location
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, "config", "simulation_config.json")

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = self._default_config()

        self._load_parameters()

    def _default_config(self) -> Dict[str, Any]:
        """Fallback default configuration matching process_model.md exactly."""
        return {
            "physical_coefficients": {
                "tensile": {
                    "S_base": 53.5, "T_ref": 230.0, "beta_T": 0.06, "gamma_T": 0.0035,
                    "P_ref": 100.0, "beta_P": 4.50, "alpha_M": 1.40, "lambda_M": 14.0,
                    "t_ref": 20.0, "kappa_cool": 2.50, "C_ref": 25.0, "theta_rec": 0.08,
                    "MFI_ref": 22.0, "T_span": 25.0, "MFI_span": 8.0, "kappa_int": 1.80,
                    "noise_sigma": 0.35
                },
                "shrinkage": {
                    "V_0": 1.15, "T_ref": 230.0, "alpha_V": 0.008, "P_ref": 100.0,
                    "beta_V": 0.45, "gamma_V": 1.20, "tau_cool": 8.0, "M_ref": 0.15,
                    "delta_M": 0.60, "C_ref": 25.0, "eta_rec": 0.005, "noise_sigma": 0.035
                },
                "energy": {
                    "E_0": 0.20, "c_thermal": 0.008, "c_hydraulic": 0.009, "c_dwell": 0.030
                }
            },
            "quality_targets": {
                "tensile_strength_mpa": {"target": 52.0, "spec_min": 49.0, "spec_max": 55.0},
                "volumetric_shrinkage_pct": {"target": 1.20, "spec_min": 0.80, "spec_max": 1.60},
                "energy_kwh": {"max_acceptable": 4.20, "nominal": 3.15}
            },
            "process_parameters": {
                "melt_temp_c": {"nominal_sop": 230.0, "min_bound": 205.0, "max_bound": 255.0},
                "injection_pressure_mpa": {"nominal_sop": 100.0, "min_bound": 65.0, "max_bound": 145.0},
                "cooling_time_s": {"nominal_sop": 20.0, "min_bound": 12.0, "max_bound": 32.0}
            }
        }

    def _load_parameters(self) -> None:
        """Cache coefficients into fast instance attributes."""
        t_coeffs = self.config["physical_coefficients"]["tensile"]
        self.S_base = float(t_coeffs["S_base"])
        self.T_ref = float(t_coeffs["T_ref"])
        self.beta_T = float(t_coeffs["beta_T"])
        self.gamma_T = float(t_coeffs["gamma_T"])
        self.P_ref = float(t_coeffs["P_ref"])
        self.beta_P = float(t_coeffs["beta_P"])
        self.alpha_M = float(t_coeffs["alpha_M"])
        self.lambda_M = float(t_coeffs["lambda_M"])
        self.t_ref = float(t_coeffs["t_ref"])
        self.kappa_cool = float(t_coeffs["kappa_cool"])
        self.C_ref = float(t_coeffs["C_ref"])
        self.theta_rec = float(t_coeffs["theta_rec"])
        self.MFI_ref = float(t_coeffs["MFI_ref"])
        self.T_span = float(t_coeffs["T_span"])
        self.MFI_span = float(t_coeffs["MFI_span"])
        self.kappa_int = float(t_coeffs["kappa_int"])
        self.noise_sigma_S = float(t_coeffs["noise_sigma"])

        s_coeffs = self.config["physical_coefficients"]["shrinkage"]
        self.V_0 = float(s_coeffs["V_0"])
        self.alpha_V = float(s_coeffs["alpha_V"])
        self.beta_V = float(s_coeffs["beta_V"])
        self.gamma_V = float(s_coeffs["gamma_V"])
        self.tau_cool = float(s_coeffs["tau_cool"])
        self.M_ref = float(s_coeffs["M_ref"])
        self.delta_M = float(s_coeffs["delta_M"])
        self.eta_rec = float(s_coeffs["eta_rec"])
        self.noise_sigma_V = float(s_coeffs["noise_sigma"])

        e_coeffs = self.config["physical_coefficients"]["energy"]
        self.E_0 = float(e_coeffs["E_0"])
        self.c_thermal = float(e_coeffs["c_thermal"])
        self.c_hydraulic = float(e_coeffs["c_hydraulic"])
        self.c_dwell = float(e_coeffs["c_dwell"])

        targets = self.config["quality_targets"]
        self.spec_S_min = float(targets["tensile_strength_mpa"]["spec_min"])
        self.spec_S_max = float(targets["tensile_strength_mpa"]["spec_max"])
        self.spec_V_min = float(targets["volumetric_shrinkage_pct"]["spec_min"])
        self.spec_V_max = float(targets["volumetric_shrinkage_pct"]["spec_max"])

    def validate_inputs(
        self,
        moisture_pct: float,
        melt_flow_index: float,
        ambient_temp_c: float,
        recycled_pct: float,
        melt_temp_c: float,
        injection_pressure_mpa: float,
        cooling_time_s: float
    ) -> None:
        """Validate input domains and prevent unphysical/NaN values."""
        inputs = [
            moisture_pct, melt_flow_index, ambient_temp_c, recycled_pct,
            melt_temp_c, injection_pressure_mpa, cooling_time_s
        ]
        if any(np.isnan(v) or np.isinf(v) for v in inputs):
            raise ValueError(f"Input contains NaN or Inf: {inputs}")

        if moisture_pct < 0.0:
            raise ValueError(f"Moisture content cannot be negative: {moisture_pct} wt %")
        if melt_flow_index <= 0.0:
            raise ValueError(f"Melt Flow Index must be positive: {melt_flow_index} g/10 min")
        if ambient_temp_c < -50.0 or ambient_temp_c > 70.0:
            raise ValueError(f"Ambient temperature unphysical: {ambient_temp_c} deg C")
        if recycled_pct < 0.0 or recycled_pct > 100.0:
            raise ValueError(f"Recycled percentage must be in [0, 100]: {recycled_pct} wt %")
        if melt_temp_c < 100.0 or melt_temp_c > 350.0:
            raise ValueError(f"Melt temperature unphysical: {melt_temp_c} deg C")
        if injection_pressure_mpa <= 0.0 or injection_pressure_mpa > 300.0:
            raise ValueError(f"Injection pressure unphysical: {injection_pressure_mpa} MPa")
        if cooling_time_s <= 0.0 or cooling_time_s > 120.0:
            raise ValueError(f"Cooling time unphysical: {cooling_time_s} s")

    def evaluate_single(
        self,
        moisture_pct: float,
        melt_flow_index: float,
        ambient_temp_c: float,
        recycled_pct: float,
        melt_temp_c: float,
        injection_pressure_mpa: float,
        cooling_time_s: float,
        add_noise: bool = True,
        rng: Optional[np.random.Generator] = None
    ) -> SimulationResult:
        """
        Evaluate a single injection molding cycle.

        Returns:
            SimulationResult containing tensile strength, shrinkage, energy, and in-spec flags.
        """
        self.validate_inputs(
            moisture_pct, melt_flow_index, ambient_temp_c, recycled_pct,
            melt_temp_c, injection_pressure_mpa, cooling_time_s
        )

        # 1. Tensile Strength Calculation (S)
        delta_T = melt_temp_c - self.T_ref
        term_therm = self.beta_T * delta_T - self.gamma_T * (delta_T ** 2)
        term_press = self.beta_P * np.log(injection_pressure_mpa / self.P_ref)
        term_moist = self.lambda_M * (moisture_pct ** self.alpha_M)
        
        # Cooling penalty: applies when dwell time is below reference
        cooling_deficit = (cooling_time_s - self.t_ref) / self.t_ref
        term_cool = self.kappa_cool * (cooling_deficit ** 2) if cooling_time_s < self.t_ref else 0.0
        
        term_rec = self.theta_rec * (recycled_pct - self.C_ref)
        term_int = self.kappa_int * (delta_T / self.T_span) * ((self.MFI_ref - melt_flow_index) / self.MFI_span)

        noise_S = 0.0
        noise_V = 0.0
        if add_noise:
            if rng is None:
                rng = np.random.default_rng()
            noise_S = rng.normal(0.0, self.noise_sigma_S)
            noise_V = rng.normal(0.0, self.noise_sigma_V)

        S = (self.S_base + term_therm + term_press - term_moist - 
             term_cool - term_rec + term_int + noise_S)

        # 2. Volumetric Shrinkage Calculation (V_sh)
        term_sh_T = self.alpha_V * delta_T
        term_sh_P = self.beta_V * ((injection_pressure_mpa - self.P_ref) / self.P_ref)
        term_sh_cool = self.gamma_V * np.exp(-cooling_time_s / self.tau_cool)
        term_sh_moist = self.delta_M * (moisture_pct - self.M_ref)
        term_sh_rec = self.eta_rec * (recycled_pct - self.C_ref)

        V_sh = (self.V_0 + term_sh_T - term_sh_P + term_sh_cool + 
                term_sh_moist - term_sh_rec + noise_V)

        # 3. Specific Process Energy (E_proc)
        temp_delta_ambient = max(0.0, melt_temp_c - ambient_temp_c)
        E_proc = (self.E_0 + 
                  self.c_thermal * temp_delta_ambient + 
                  self.c_hydraulic * (injection_pressure_mpa / self.P_ref) + 
                  self.c_dwell * cooling_time_s)

        # In-Spec Evaluations
        s_ok = int(self.spec_S_min <= S <= self.spec_S_max)
        v_ok = int(self.spec_V_min <= V_sh <= self.spec_V_max)
        in_spec = int(s_ok and v_ok)

        # Target Infeasibility Flag (e.g. moisture exceeds physically compensable threshold)
        infeasible = int(moisture_pct > 0.65 or S < (self.spec_S_min - 3.0))

        return SimulationResult(
            tensile_strength_mpa=float(S),
            volumetric_shrinkage_pct=float(V_sh),
            energy_kwh=float(E_proc),
            in_spec_flag=in_spec,
            tensile_in_spec=s_ok,
            shrinkage_in_spec=v_ok,
            target_infeasible_flag=infeasible
        )

    def evaluate_batch(
        self,
        df: pd.DataFrame,
        add_noise: bool = True,
        seed: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Vectorized / batched simulation evaluation over a DataFrame of operating cycles.

        Required columns in df:
          - moisture_pct
          - melt_flow_index
          - ambient_temp_c
          - recycled_pct
          - melt_temp_c
          - injection_pressure_mpa
          - cooling_time_s
        """
        required_cols = [
            "moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct",
            "melt_temp_c", "injection_pressure_mpa", "cooling_time_s"
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise KeyError(f"DataFrame is missing required columns: {missing}")

        n = len(df)
        rng = np.random.default_rng(seed)

        # Extract arrays
        M = df["moisture_pct"].to_numpy(dtype=float)
        MFI = df["melt_flow_index"].to_numpy(dtype=float)
        T_amb = df["ambient_temp_c"].to_numpy(dtype=float)
        C_rec = df["recycled_pct"].to_numpy(dtype=float)
        T_melt = df["melt_temp_c"].to_numpy(dtype=float)
        P_inj = df["injection_pressure_mpa"].to_numpy(dtype=float)
        t_cool = df["cooling_time_s"].to_numpy(dtype=float)

        # Vectorized Tensile
        delta_T = T_melt - self.T_ref
        term_therm = self.beta_T * delta_T - self.gamma_T * (delta_T ** 2)
        term_press = self.beta_P * np.log(P_inj / self.P_ref)
        term_moist = self.lambda_M * (M ** self.alpha_M)
        
        cooling_deficit = np.maximum(0.0, (self.t_ref - t_cool) / self.t_ref)
        term_cool = self.kappa_cool * (cooling_deficit ** 2)
        
        term_rec = self.theta_rec * (C_rec - self.C_ref)
        term_int = self.kappa_int * (delta_T / self.T_span) * ((self.MFI_ref - MFI) / self.MFI_span)

        noise_S = rng.normal(0.0, self.noise_sigma_S, size=n) if add_noise else np.zeros(n)
        noise_V = rng.normal(0.0, self.noise_sigma_V, size=n) if add_noise else np.zeros(n)

        S = (self.S_base + term_therm + term_press - term_moist - 
             term_cool - term_rec + term_int + noise_S)

        # Vectorized Shrinkage
        term_sh_T = self.alpha_V * delta_T
        term_sh_P = self.beta_V * ((P_inj - self.P_ref) / self.P_ref)
        term_sh_cool = self.gamma_V * np.exp(-t_cool / self.tau_cool)
        term_sh_moist = self.delta_M * (M - self.M_ref)
        term_sh_rec = self.eta_rec * (C_rec - self.C_ref)

        V_sh = (self.V_0 + term_sh_T - term_sh_P + term_sh_cool + 
                term_sh_moist - term_sh_rec + noise_V)

        # Vectorized Energy
        temp_delta_amb = np.maximum(0.0, T_melt - T_amb)
        E_proc = (self.E_0 + 
                  self.c_thermal * temp_delta_amb + 
                  self.c_hydraulic * (P_inj / self.P_ref) + 
                  self.c_dwell * t_cool)

        s_ok = (S >= self.spec_S_min) & (S <= self.spec_S_max)
        v_ok = (V_sh >= self.spec_V_min) & (V_sh <= self.spec_V_max)
        in_spec = s_ok & v_ok
        infeasible = (M > 0.65) | (S < (self.spec_S_min - 3.0))

        out_df = df.copy()
        out_df["tensile_strength_mpa"] = S
        out_df["volumetric_shrinkage_pct"] = V_sh
        out_df["energy_kwh"] = E_proc
        out_df["in_spec_flag"] = in_spec.astype(int)
        out_df["tensile_in_spec"] = s_ok.astype(int)
        out_df["shrinkage_in_spec"] = v_ok.astype(int)
        out_df["target_infeasible_flag"] = infeasible.astype(int)

        return out_df
