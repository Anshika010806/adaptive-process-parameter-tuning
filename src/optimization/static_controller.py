"""
Static Controller (Standard Operating Procedure / SOP Baseline).

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
"""

from __future__ import annotations
import json
import os
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from src.simulation.process_simulator import PolymerInjectionSimulator


class StaticSOPController:
    """
    Standard Operating Procedure (SOP) Fixed-Settings Controller.

    Represents standard factory practice where machine actuators are maintained
    at fixed nominal configurations validated under nominal conditions, completely
    ignoring incoming batch material variability.

    Nominal Setpoints:
      - T_melt = 230.0 deg C
      - P_inj  = 100.0 MPa
      - t_cool = 20.0 s
    """

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, "config", "simulation_config.json")

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            p_cfg = config["process_parameters"]
            self.melt_temp_c = float(p_cfg["melt_temp_c"]["nominal_sop"])
            self.injection_pressure_mpa = float(p_cfg["injection_pressure_mpa"]["nominal_sop"])
            self.cooling_time_s = float(p_cfg["cooling_time_s"]["nominal_sop"])
        else:
            self.melt_temp_c = 230.0
            self.injection_pressure_mpa = 100.0
            self.cooling_time_s = 20.0

    def recommend(self, material_inputs: Dict[str, float]) -> Dict[str, float]:
        """
        Produce actuator recommendations for given material disturbance.
        Static controller unconditionally outputs nominal settings.
        """
        return {
            "melt_temp_c": self.melt_temp_c,
            "injection_pressure_mpa": self.injection_pressure_mpa,
            "cooling_time_s": self.cooling_time_s,
        }

    def evaluate_batch(
        self,
        df: pd.DataFrame,
        simulator: PolymerInjectionSimulator,
        add_noise: bool = True,
        seed: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Apply static settings to a batch of material disturbance cycles
        and evaluate realized physical outcomes using the true simulator.
        """
        n = len(df)
        df_eval = df.copy()
        df_eval["melt_temp_c"] = self.melt_temp_c
        df_eval["injection_pressure_mpa"] = self.injection_pressure_mpa
        df_eval["cooling_time_s"] = self.cooling_time_s

        return simulator.evaluate_batch(df_eval, add_noise=add_noise, seed=seed)
