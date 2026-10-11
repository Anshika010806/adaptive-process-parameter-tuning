"""
Synthetic Data Generation Engine for Polymer Injection Molding.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
"""

from __future__ import annotations
import os
import json
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from .process_simulator import PolymerInjectionSimulator


class DataGenerator:
    """
    Generates reproducible synthetic datasets for model training, validation,
    and out-of-distribution (OOD) generalization studies.
    """

    def __init__(self, simulator: Optional[PolymerInjectionSimulator] = None):
        self.simulator = simulator or PolymerInjectionSimulator()
        self.config = self.simulator.config

    def sample_material_inputs_id(
        self,
        n: int,
        seed: int
    ) -> pd.DataFrame:
        """Sample material conditions under In-Distribution (ID) regime."""
        rng = np.random.default_rng(seed)

        # 1. Moisture (wt %): Truncated Gaussian in [0.05, 0.45] around nominal 0.15
        M = rng.normal(loc=0.15, scale=0.06, size=n)
        M = np.clip(M, 0.05, 0.45)

        # 2. MFI (g/10 min): Truncated Gaussian in [14.0, 30.0] around nominal 22.0
        MFI = rng.normal(loc=22.0, scale=3.0, size=n)
        MFI = np.clip(MFI, 14.0, 30.0)

        # 3. Ambient Temp (deg C): Truncated Gaussian in [18.0, 30.0] around nominal 24.0
        T_amb = rng.normal(loc=24.0, scale=2.5, size=n)
        T_amb = np.clip(T_amb, 18.0, 30.0)

        # 4. Recycled Content (wt %): Beta distribution in [10.0, 40.0] around nominal 25.0
        beta_raw = rng.beta(a=2.5, b=2.5, size=n)
        C_rec = 10.0 + beta_raw * 30.0

        return pd.DataFrame({
            "moisture_pct": M,
            "melt_flow_index": MFI,
            "ambient_temp_c": T_amb,
            "recycled_pct": C_rec
        })

    def sample_process_controls_exploration(
        self,
        n: int,
        seed: int
    ) -> pd.DataFrame:
        """Sample process parameters uniformly across operational bounds for surrogate exploration."""
        rng = np.random.default_rng(seed)

        # Operational bounds
        p_cfg = self.config["process_parameters"]
        T_melt = rng.uniform(
            p_cfg["melt_temp_c"]["min_bound"],
            p_cfg["melt_temp_c"]["max_bound"],
            size=n
        )
        P_inj = rng.uniform(
            p_cfg["injection_pressure_mpa"]["min_bound"],
            p_cfg["injection_pressure_mpa"]["max_bound"],
            size=n
        )
        t_cool = rng.uniform(
            p_cfg["cooling_time_s"]["min_bound"],
            p_cfg["cooling_time_s"]["max_bound"],
            size=n
        )

        return pd.DataFrame({
            "melt_temp_c": T_melt,
            "injection_pressure_mpa": P_inj,
            "cooling_time_s": t_cool
        })

    def sample_process_controls_sop(self, n: int) -> pd.DataFrame:
        """Sample fixed Standard Operating Procedure (SOP) nominal settings."""
        p_cfg = self.config["process_parameters"]
        return pd.DataFrame({
            "melt_temp_c": np.full(n, p_cfg["melt_temp_c"]["nominal_sop"]),
            "injection_pressure_mpa": np.full(n, p_cfg["injection_pressure_mpa"]["nominal_sop"]),
            "cooling_time_s": np.full(n, p_cfg["cooling_time_s"]["nominal_sop"])
        })

    def generate_in_distribution_dataset(
        self,
        n: int,
        seed: int,
        explore_controls: bool = True
    ) -> pd.DataFrame:
        """Generate a complete in-distribution dataset."""
        df_mat = self.sample_material_inputs_id(n, seed=seed)
        if explore_controls:
            df_ctrl = self.sample_process_controls_exploration(n, seed=seed + 1000)
        else:
            df_ctrl = self.sample_process_controls_sop(n)

        df_combined = pd.concat([df_mat, df_ctrl], axis=1)
        df_sim = self.simulator.evaluate_batch(df_combined, add_noise=True, seed=seed + 2000)
        df_sim.insert(0, "cycle_id", np.arange(1, n + 1))
        return df_sim

    def generate_ood_1_feedstock_shift(self, n: int = 500, seed: int = 301) -> pd.DataFrame:
        """OOD-1: Feedstock degradation shift (high moisture, low MFI)."""
        rng = np.random.default_rng(seed)
        M = np.clip(rng.normal(loc=0.42, scale=0.05, size=n), 0.30, 0.55)
        MFI = np.clip(rng.normal(loc=16.0, scale=2.0, size=n), 11.0, 20.0)
        T_amb = np.clip(rng.normal(loc=24.0, scale=2.5, size=n), 18.0, 30.0)
        C_rec = 10.0 + rng.beta(2.5, 2.5, size=n) * 30.0

        df_mat = pd.DataFrame({
            "moisture_pct": M,
            "melt_flow_index": MFI,
            "ambient_temp_c": T_amb,
            "recycled_pct": C_rec
        })
        df_ctrl = self.sample_process_controls_sop(n)
        df_combined = pd.concat([df_mat, df_ctrl], axis=1)
        df_sim = self.simulator.evaluate_batch(df_combined, add_noise=True, seed=seed + 100)
        df_sim.insert(0, "cycle_id", np.arange(1, n + 1))
        return df_sim

    def generate_ood_2_thermal_shift(self, n: int = 500, seed: int = 302) -> pd.DataFrame:
        """OOD-2: Factory thermal heatwave shift (extreme ambient temperatures)."""
        rng = np.random.default_rng(seed)
        M = np.clip(rng.normal(loc=0.15, scale=0.06, size=n), 0.05, 0.45)
        MFI = np.clip(rng.normal(loc=22.0, scale=3.0, size=n), 14.0, 30.0)
        T_amb = np.clip(rng.normal(loc=36.5, scale=2.0, size=n), 33.0, 42.0)
        C_rec = 10.0 + rng.beta(2.5, 2.5, size=n) * 30.0

        df_mat = pd.DataFrame({
            "moisture_pct": M,
            "melt_flow_index": MFI,
            "ambient_temp_c": T_amb,
            "recycled_pct": C_rec
        })
        df_ctrl = self.sample_process_controls_sop(n)
        df_combined = pd.concat([df_mat, df_ctrl], axis=1)
        df_sim = self.simulator.evaluate_batch(df_combined, add_noise=True, seed=seed + 100)
        df_sim.insert(0, "cycle_id", np.arange(1, n + 1))
        return df_sim

    def generate_ood_3_extrapolation(self, n: int = 500, seed: int = 303) -> pd.DataFrame:
        """OOD-3: Extrapolation beyond training support (moisture in [0.55, 0.70] wt %)."""
        rng = np.random.default_rng(seed)
        M = rng.uniform(0.55, 0.70, size=n)
        MFI = np.clip(rng.normal(loc=22.0, scale=3.0, size=n), 14.0, 30.0)
        T_amb = np.clip(rng.normal(loc=24.0, scale=2.5, size=n), 18.0, 30.0)
        C_rec = 10.0 + rng.beta(2.5, 2.5, size=n) * 30.0

        df_mat = pd.DataFrame({
            "moisture_pct": M,
            "melt_flow_index": MFI,
            "ambient_temp_c": T_amb,
            "recycled_pct": C_rec
        })
        df_ctrl = self.sample_process_controls_sop(n)
        df_combined = pd.concat([df_mat, df_ctrl], axis=1)
        df_sim = self.simulator.evaluate_batch(df_combined, add_noise=True, seed=seed + 100)
        df_sim.insert(0, "cycle_id", np.arange(1, n + 1))
        return df_sim

    def generate_ood_4_sensor_noise(self, n: int = 500, seed: int = 304) -> pd.DataFrame:
        """OOD-4: Sensor noise / observation corruption (15% measurement noise)."""
        rng = np.random.default_rng(seed)
        df_base = self.sample_material_inputs_id(n, seed=seed)

        # Corrupt measured material values
        noisy_M = np.clip(df_base["moisture_pct"] * (1.0 + rng.normal(0, 0.15, n)), 0.01, 0.60)
        noisy_MFI = np.clip(df_base["melt_flow_index"] * (1.0 + rng.normal(0, 0.15, n)), 10.0, 35.0)

        df_mat_corrupted = df_base.copy()
        df_mat_corrupted["moisture_pct"] = noisy_M
        df_mat_corrupted["melt_flow_index"] = noisy_MFI

        df_ctrl = self.sample_process_controls_sop(n)
        df_combined = pd.concat([df_mat_corrupted, df_ctrl], axis=1)
        df_sim = self.simulator.evaluate_batch(df_combined, add_noise=True, seed=seed + 100)
        df_sim.insert(0, "cycle_id", np.arange(1, n + 1))
        return df_sim

    def generate_and_save_all(self, output_dir: str) -> Dict[str, str]:
        """Generate and persist train, val, test, and all 4 OOD benchmark files."""
        os.makedirs(output_dir, exist_ok=True)
        seeds = self.config["random_seeds"]

        paths = {}
        # 1. In-distribution exploration data for model training
        df_train = self.generate_in_distribution_dataset(3500, seed=seeds["train"], explore_controls=True)
        train_path = os.path.join(output_dir, "dataset_train.csv")
        df_train.to_csv(train_path, index=False)
        paths["train"] = train_path

        # 2. Validation set
        df_val = self.generate_in_distribution_dataset(750, seed=seeds["val"], explore_controls=True)
        val_path = os.path.join(output_dir, "dataset_val.csv")
        df_val.to_csv(val_path, index=False)
        paths["val"] = val_path

        # 3. Test set (In-distribution held-out)
        df_test_id = self.generate_in_distribution_dataset(750, seed=seeds["test_id"], explore_controls=True)
        test_path = os.path.join(output_dir, "dataset_test_id.csv")
        df_test_id.to_csv(test_path, index=False)
        paths["test_id"] = test_path

        # 4. OOD Scenarios (under SOP baseline control)
        df_ood1 = self.generate_ood_1_feedstock_shift(500, seed=seeds["ood_1_feedstock"])
        ood1_path = os.path.join(output_dir, "dataset_ood_1_feedstock.csv")
        df_ood1.to_csv(ood1_path, index=False)
        paths["ood_1"] = ood1_path

        df_ood2 = self.generate_ood_2_thermal_shift(500, seed=seeds["ood_2_thermal"])
        ood2_path = os.path.join(output_dir, "dataset_ood_2_thermal.csv")
        df_ood2.to_csv(ood2_path, index=False)
        paths["ood_2"] = ood2_path

        df_ood3 = self.generate_ood_3_extrapolation(500, seed=seeds["ood_3_extrap"])
        ood3_path = os.path.join(output_dir, "dataset_ood_3_extrap.csv")
        df_ood3.to_csv(ood3_path, index=False)
        paths["ood_3"] = ood3_path

        df_ood4 = self.generate_ood_4_sensor_noise(500, seed=seeds["ood_4_sensor"])
        ood4_path = os.path.join(output_dir, "dataset_ood_4_sensor.csv")
        df_ood4.to_csv(ood4_path, index=False)
        paths["ood_4"] = ood4_path

        return paths
