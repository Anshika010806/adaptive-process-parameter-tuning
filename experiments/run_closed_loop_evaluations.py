# -*- coding: utf-8 -*-
"""
Experiment Execution: Independent Closed-Loop Controller Evaluation.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 3)
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
import joblib

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.simulation.process_simulator import PolymerInjectionSimulator
from src.optimization.static_controller import StaticSOPController
from src.optimization.adaptive_tuner import AdaptiveProcessTuner


def format_table(rows, headers):
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))

    header_str = " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
    sep_str = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    row_strs = [
        " | ".join(f"{str(val):<{col_widths[i]}}" for i, val in enumerate(row))
        for row in rows
    ]
    return f"{header_str}\n{sep_str}\n" + "\n".join(row_strs)


def evaluate_stream(
    stream_name: str,
    df_material: pd.DataFrame,
    adaptive_tuner: AdaptiveProcessTuner,
    static_controller: StaticSOPController,
    simulator: PolymerInjectionSimulator,
    seeds: list[int]
) -> dict:
    """
    Execute matched-pair evaluation of Static SOP vs Adaptive Tuner across multiple seeds.
    """
    material_cols = ["moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct"]
    df_mat_clean = df_material[material_cols].copy()

    # 1. Obtain Adaptive Tuner recommendations using vectorized tune_batch
    t0 = time.perf_counter()
    df_tuned = adaptive_tuner.tune_batch(df_mat_clean)
    tuning_time_s = time.perf_counter() - t0

    df_adaptive_inputs = df_mat_clean.copy()
    df_adaptive_inputs["melt_temp_c"] = df_tuned["melt_temp_c"].to_numpy()
    df_adaptive_inputs["injection_pressure_mpa"] = df_tuned["injection_pressure_mpa"].to_numpy()
    df_adaptive_inputs["cooling_time_s"] = df_tuned["cooling_time_s"].to_numpy()

    feasibility_pct = df_tuned["is_feasible"].mean() * 100.0

    # 2. Obtain Static SOP inputs
    df_sop_inputs = df_mat_clean.copy()
    df_sop_inputs["melt_temp_c"] = static_controller.melt_temp_c
    df_sop_inputs["injection_pressure_mpa"] = static_controller.injection_pressure_mpa
    df_sop_inputs["cooling_time_s"] = static_controller.cooling_time_s

    # 3. True simulator evaluation across multiple seeds for variability
    sop_yields, adaptive_yields = [], []
    sop_energies, adaptive_energies = [], []
    sop_tens_viol, adaptive_tens_viol = [], []
    sop_shrink_viol, adaptive_shrink_viol = [], []

    for seed in seeds:
        # Evaluate Static SOP
        res_sop = simulator.evaluate_batch(df_sop_inputs, add_noise=True, seed=seed)
        sop_yield = res_sop["in_spec_flag"].mean() * 100.0
        sop_yields.append(sop_yield)
        sop_energies.append(res_sop["energy_kwh"].mean())
        sop_tens_viol.append((1.0 - res_sop["tensile_in_spec"].mean()) * 100.0)
        sop_shrink_viol.append((1.0 - res_sop["shrinkage_in_spec"].mean()) * 100.0)

        # Evaluate Adaptive Controller
        res_adapt = simulator.evaluate_batch(df_adaptive_inputs, add_noise=True, seed=seed)
        adapt_yield = res_adapt["in_spec_flag"].mean() * 100.0
        adaptive_yields.append(adapt_yield)
        adaptive_energies.append(res_adapt["energy_kwh"].mean())
        adaptive_tens_viol.append((1.0 - res_adapt["tensile_in_spec"].mean()) * 100.0)
        adaptive_shrink_viol.append((1.0 - res_adapt["shrinkage_in_spec"].mean()) * 100.0)

    delta_yield_mean = float(np.mean(adaptive_yields) - np.mean(sop_yields))
    delta_energy_pct = float(((np.mean(adaptive_energies) - np.mean(sop_energies)) / np.mean(sop_energies)) * 100.0)

    return {
        "stream_name": stream_name,
        "n_samples": len(df_mat_clean),
        "feasibility_pct": feasibility_pct,
        "tuning_time_sec": tuning_time_s,
        "sop_yield_mean": float(np.mean(sop_yields)),
        "sop_yield_std": float(np.std(sop_yields)),
        "adaptive_yield_mean": float(np.mean(adaptive_yields)),
        "adaptive_yield_std": float(np.std(adaptive_yields)),
        "delta_yield": delta_yield_mean,
        "sop_energy_mean": float(np.mean(sop_energies)),
        "adaptive_energy_mean": float(np.mean(adaptive_energies)),
        "delta_energy_pct": delta_energy_pct,
        "sop_tensile_viol_pct": float(np.mean(sop_tens_viol)),
        "adaptive_tensile_viol_pct": float(np.mean(adaptive_tens_viol)),
        "sop_shrinkage_viol_pct": float(np.mean(sop_shrink_viol)),
        "adaptive_shrinkage_viol_pct": float(np.mean(adaptive_shrink_viol)),
        "seeds_evaluated": seeds
    }


def main():
    print("=" * 80)
    print("Worklet No. 28 - PBL-II Milestone: Independent Closed-Loop Evaluation")
    print("=" * 80)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data", "synthetic")
    models_dir = os.path.join(base_dir, "models")
    results_path = os.path.join(base_dir, "data", "closed_loop_evaluation_results.json")

    rf_model_path = os.path.join(models_dir, "surrogate_randomforest.joblib")
    if not os.path.exists(rf_model_path):
        raise FileNotFoundError(f"Trained Random Forest surrogate not found at: {rf_model_path}")

    surrogate_rf = joblib.load(rf_model_path)
    tuner = AdaptiveProcessTuner(surrogate_pipeline=surrogate_rf)
    static_ctrl = StaticSOPController()
    simulator = PolymerInjectionSimulator()

    streams = {
        "Nominal ID Test Set": "dataset_test_id.csv",
        "OOD-1 (Feedstock Degradation)": "dataset_ood_1_feedstock.csv",
        "OOD-2 (Shop-Floor Heatwave)": "dataset_ood_2_thermal.csv",
        "OOD-3 (Moisture Extrapolation)": "dataset_ood_3_extrap.csv",
        "OOD-4 (Sensor Noise 15%)": "dataset_ood_4_sensor.csv"
    }

    seeds = [1001, 1002, 1003]
    all_results = {}

    print(f"\nExecuting closed-loop simulation over {len(streams)} streams across seeds {seeds}...\n")

    table_rows = []
    headers = [
        "Evaluation Stream", "SOP Yield", "Adaptive Yield", "dYield",
        "SOP Energy", "Adapt Energy", "dEnergy%", "Feasibility"
    ]

    for stream_name, filename in streams.items():
        filepath = os.path.join(data_dir, filename)
        df_stream = pd.read_csv(filepath)
        res = evaluate_stream(
            stream_name=stream_name,
            df_material=df_stream,
            adaptive_tuner=tuner,
            static_controller=static_ctrl,
            simulator=simulator,
            seeds=seeds
        )
        all_results[stream_name] = res

        table_rows.append([
            stream_name,
            f"{res['sop_yield_mean']:.1f}% ± {res['sop_yield_std']:.1f}%",
            f"{res['adaptive_yield_mean']:.1f}% ± {res['adaptive_yield_std']:.1f}%",
            f"{res['delta_yield']:+.1f}%",
            f"{res['sop_energy_mean']:.2f} kWh",
            f"{res['adaptive_energy_mean']:.2f} kWh",
            f"{res['delta_energy_pct']:+.1f}%",
            f"{res['feasibility_pct']:.1f}%"
        ])

    print("=" * 80)
    print("CLOSED-LOOP TRUE SIMULATOR PERFORMANCE MATRIX (Matched Disturbances)")
    print("=" * 80)
    print(format_table(table_rows, headers))

    # Detailed defect breakdown table
    print("\n" + "=" * 80)
    print("DEFECT BREAKDOWN COMPARISON (Tensile vs Shrinkage Violations)")
    print("=" * 80)
    defect_headers = ["Stream", "SOP Tensile Viol", "Adapt Tensile Viol", "SOP Shrink Viol", "Adapt Shrink Viol"]
    defect_rows = []
    for stream_name, r in all_results.items():
        defect_rows.append([
            stream_name,
            f"{r['sop_tensile_viol_pct']:.1f}%",
            f"{r['adaptive_tensile_viol_pct']:.1f}%",
            f"{r['sop_shrinkage_viol_pct']:.1f}%",
            f"{r['adaptive_shrinkage_viol_pct']:.1f}%"
        ])
    print(format_table(defect_rows, defect_headers))

    # Save to JSON
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved closed-loop evaluation results payload to: {results_path}")


if __name__ == "__main__":
    main()
