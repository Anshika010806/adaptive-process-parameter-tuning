"""
Experiment Runner: Working Baseline Models and Static Controller (PBL-I).

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
"""

import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from src.simulation.process_simulator import PolymerInjectionSimulator
from src.models.baseline import BaselineRegressor, BaselineMetrics
from src.optimization.static_controller import StaticSOPController


def main():
    print("=" * 80)
    print("Worklet No. 28 - AI-Based Adaptive Process Parameter Tuning")
    print("Phase 2 Experiment: Working Baseline Models & Static SOP Controller (PBL-I)")
    print("=" * 80)

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic")
    train_df = pd.read_csv(os.path.join(data_dir, "dataset_train.csv"))
    test_df = pd.read_csv(os.path.join(data_dir, "dataset_test_id.csv"))

    print(f"\n1. Datasets Loaded:")
    print(f"   - Training fold: {len(train_df)} samples")
    print(f"   - Held-out test fold: {len(test_df)} samples")

    # Train Baseline Models
    models = {
        "Dummy (Mean)": BaselineRegressor(model_type="dummy"),
        "Linear Regression": BaselineRegressor(model_type="linear"),
        "Ridge Regression (alpha=1.0)": BaselineRegressor(model_type="ridge", alpha=1.0),
    }

    results = []
    print("\n2. Evaluating Multi-Output Quality Prediction Surrogates:")
    print(f"   {'Model Name':<28s} | {'Tensile MAE':<11s} | {'Tensile R2':<10s} | {'Shrink MAE':<10s} | {'Shrink R2':<10s}")
    print("   " + "-" * 76)

    for name, model in models.items():
        model.fit(train_df, train_df)
        m = model.evaluate(test_df, test_df, n_train=len(train_df))
        results.append(m)
        print(f"   {name:<28s} | {m.tensile_mae:7.3f} MPa | {m.tensile_r2:9.3f}  | {m.shrinkage_mae:6.3f} %   | {m.shrinkage_r2:9.3f}")

    # Evaluate Static SOP Controller
    print("\n3. Evaluating Static SOP Fixed-Recipe Controller on Held-Out Test Stream:")
    controller = StaticSOPController()
    simulator = PolymerInjectionSimulator()

    mat_cols = ["moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct"]
    df_evaluated = controller.evaluate_batch(test_df[mat_cols], simulator=simulator, add_noise=True, seed=42)

    in_spec_pct = df_evaluated["in_spec_flag"].mean() * 100.0
    defect_pct = 100.0 - in_spec_pct
    mean_tensile = df_evaluated["tensile_strength_mpa"].mean()
    mean_shrinkage = df_evaluated["volumetric_shrinkage_pct"].mean()
    mean_energy = df_evaluated["energy_kwh"].mean()

    print(f"   - Fixed SOP Melt Temperature:        {controller.melt_temp_c:.1f} deg C")
    print(f"   - Fixed SOP Injection Pressure:      {controller.injection_pressure_mpa:.1f} MPa")
    print(f"   - Fixed SOP Cooling Dwell Time:      {controller.cooling_time_s:.1f} s")
    print(f"   - Realized In-Spec Quality Yield:    {in_spec_pct:.2f}%")
    print(f"   - Quality Target Defect Rate:        {defect_pct:.2f}%")
    print(f"   - Realized Mean Tensile Strength:    {mean_tensile:.2f} MPa (Target: 52.0 +/- 3.0)")
    print(f"   - Realized Mean Volumetric Shrinkage: {mean_shrinkage:.2f}% (Target: 1.20 +/- 0.40)")
    print(f"   - Realized Specific Process Energy:  {mean_energy:.2f} kWh/cycle")

    print("\n" + "=" * 80)
    print("Baseline benchmark complete. Results documented for Research Logbook EXP-002.")
    print("=" * 80)


if __name__ == "__main__":
    main()
