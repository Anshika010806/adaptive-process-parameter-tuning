"""
Experiment: Gate 4 — Feature Ablation, Robustness Testing, and Sensitivity Analysis.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 4)
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
import joblib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, root_mean_squared_error
from src.simulation.process_simulator import PolymerInjectionSimulator


def compute_metrics(y_true, y_pred):
    """Compute MAE, RMSE, R2 for tensile and shrinkage."""
    return {
        "tensile_mae": float(mean_absolute_error(y_true[:, 0], y_pred[:, 0])),
        "tensile_rmse": float(root_mean_squared_error(y_true[:, 0], y_pred[:, 0])),
        "tensile_r2": float(r2_score(y_true[:, 0], y_pred[:, 0])),
        "shrinkage_mae": float(mean_absolute_error(y_true[:, 1], y_pred[:, 1])),
        "shrinkage_rmse": float(root_mean_squared_error(y_true[:, 1], y_pred[:, 1])),
        "shrinkage_r2": float(r2_score(y_true[:, 1], y_pred[:, 1])),
    }


def format_table(rows, headers):
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
    hdr = " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
    sep = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    rows_str = [" | ".join(f"{str(v):<{col_widths[i]}}" for i, v in enumerate(r)) for r in rows]
    return f"{hdr}\n{sep}\n" + "\n".join(rows_str)


def run_feature_ablation(df_train, df_test, feature_cols, target_cols):
    """
    Feature ablation study: remove one feature at a time and measure R2 degradation.
    """
    X_train_full = df_train[feature_cols].to_numpy(dtype=float)
    y_train = df_train[target_cols].to_numpy(dtype=float)
    X_test_full = df_test[feature_cols].to_numpy(dtype=float)
    y_test = df_test[target_cols].to_numpy(dtype=float)

    # Baseline: full feature set
    pipe_full = Pipeline([("rf", RandomForestRegressor(n_estimators=100, max_depth=18, random_state=42, n_jobs=-1))])
    pipe_full.fit(X_train_full, y_train)
    base_metrics = compute_metrics(y_test, pipe_full.predict(X_test_full))

    results = [{"ablated_feature": "NONE (Baseline)", **base_metrics}]

    for feat_idx, feat_name in enumerate(feature_cols):
        remaining = [c for c in feature_cols if c != feat_name]
        X_train_abl = df_train[remaining].to_numpy(dtype=float)
        X_test_abl = df_test[remaining].to_numpy(dtype=float)

        pipe_abl = Pipeline([("rf", RandomForestRegressor(n_estimators=100, max_depth=18, random_state=42, n_jobs=-1))])
        pipe_abl.fit(X_train_abl, y_train)
        abl_metrics = compute_metrics(y_test, pipe_abl.predict(X_test_abl))
        abl_metrics["ablated_feature"] = feat_name

        # Compute R2 drop
        abl_metrics["tensile_r2_drop"] = float(base_metrics["tensile_r2"] - abl_metrics["tensile_r2"])
        abl_metrics["shrinkage_r2_drop"] = float(base_metrics["shrinkage_r2"] - abl_metrics["shrinkage_r2"])

        results.append(abl_metrics)

    return results


def run_noise_robustness(df_train, df_test, feature_cols, target_cols, noise_levels):
    """
    Additive Gaussian noise injection: test RF surrogate robustness to measurement noise.
    """
    X_train = df_train[feature_cols].to_numpy(dtype=float)
    y_train = df_train[target_cols].to_numpy(dtype=float)
    X_test_clean = df_test[feature_cols].to_numpy(dtype=float)
    y_test = df_test[target_cols].to_numpy(dtype=float)

    pipe = Pipeline([("rf", RandomForestRegressor(n_estimators=100, max_depth=18, random_state=42, n_jobs=-1))])
    pipe.fit(X_train, y_train)

    results = []
    rng = np.random.default_rng(999)

    for noise_pct in noise_levels:
        if noise_pct == 0.0:
            X_noisy = X_test_clean.copy()
        else:
            noise_std = noise_pct * np.abs(X_test_clean)
            X_noisy = X_test_clean + rng.normal(0.0, 1.0, X_test_clean.shape) * noise_std

        metrics = compute_metrics(y_test, pipe.predict(X_noisy))
        results.append({"noise_pct": f"{noise_pct * 100:.0f}%", **metrics})

    return results


def run_weight_sensitivity(df_material, surrogate, target_tensile, spec_S, target_shrink, spec_V,
                           energy_norm, actuator_candidates, bounds, sop_defaults):
    """
    Sensitivity to multi-objective weight configurations.
    Measure how 3 weight configurations (quality-first, balanced, energy-first) affect
    the distribution of recommended setpoints on a subset of nominal material inputs.
    """
    sim = PolymerInjectionSimulator()
    MATERIAL_COLS = ["moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct"]

    weight_configs = {
        "Quality-First  (w_S=0.70, w_V=0.25, w_E=0.05)": {"w_S": 0.70, "w_V": 0.25, "w_E": 0.05},
        "Balanced       (w_S=0.50, w_V=0.35, w_E=0.15)": {"w_S": 0.50, "w_V": 0.35, "w_E": 0.15},
        "Energy-First   (w_S=0.30, w_V=0.25, w_E=0.45)": {"w_S": 0.30, "w_V": 0.25, "w_E": 0.45},
    }

    results = []
    mat_vals = df_material[MATERIAL_COLS].to_numpy(dtype=float)
    n = len(mat_vals)
    n_candidates = len(actuator_candidates)

    mat_repeated = np.repeat(mat_vals, n_candidates, axis=0)
    cand_tiled = np.tile(actuator_candidates, (n, 1))
    features = np.hstack([mat_repeated, cand_tiled])

    all_preds = surrogate.predict(features)
    S_preds = all_preds[:, 0]
    V_preds = all_preds[:, 1]

    P_ref = 100.0
    E_0, c_th, c_hyd, c_dw = 0.20, 0.008, 0.009, 0.030
    E_preds = (E_0 + c_th * np.maximum(0.0, cand_tiled[:, 0] - mat_repeated[:, 2]) +
               c_hyd * (cand_tiled[:, 1] / P_ref) + c_dw * cand_tiled[:, 2])

    tol_S = (spec_S[1] - spec_S[0]) / 2.0
    tol_V = (spec_V[1] - spec_V[0]) / 2.0

    for config_name, w in weight_configs.items():
        viol_S = np.maximum(0.0, spec_S[0] - S_preds) + np.maximum(0.0, S_preds - spec_S[1])
        viol_V = np.maximum(0.0, spec_V[0] - V_preds) + np.maximum(0.0, V_preds - spec_V[1])
        penalty_scale = 100.0

        losses = (
            w["w_S"] * (((S_preds - target_tensile) / tol_S) ** 2 + penalty_scale * ((viol_S / tol_S) ** 2)) +
            w["w_V"] * (((V_preds - target_shrink) / tol_V) ** 2 + penalty_scale * ((viol_V / tol_V) ** 2)) +
            w["w_E"] * (E_preds / energy_norm)
        )

        loss_matrix = losses.reshape(n, n_candidates)
        best_idx = np.argmin(loss_matrix, axis=1)

        opt_T = actuator_candidates[best_idx, 0]
        opt_P = actuator_candidates[best_idx, 1]
        opt_C = actuator_candidates[best_idx, 2]

        df_sim_inputs = df_material[MATERIAL_COLS].copy()
        df_sim_inputs["melt_temp_c"] = opt_T
        df_sim_inputs["injection_pressure_mpa"] = opt_P
        df_sim_inputs["cooling_time_s"] = opt_C

        df_realized = sim.evaluate_batch(df_sim_inputs, add_noise=True, seed=42)
        mean_yield = df_realized["in_spec_flag"].mean() * 100.0
        mean_energy = df_realized["energy_kwh"].mean()

        results.append({
            "config": config_name,
            "mean_yield_pct": round(mean_yield, 1),
            "mean_energy_kwh": round(mean_energy, 3),
            "mean_T_melt": round(opt_T.mean(), 1),
            "mean_P_inj": round(opt_P.mean(), 1),
            "mean_t_cool": round(opt_C.mean(), 1)
        })

    return results


def main():
    print("=" * 80)
    print("Worklet No. 28 - Gate 4: Feature Ablation, Noise Robustness, Weight Sensitivity")
    print("=" * 80)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data", "synthetic")
    results_path = os.path.join(base_dir, "data", "ablation_results.json")

    feature_cols = [
        "moisture_pct", "melt_flow_index", "ambient_temp_c", "recycled_pct",
        "melt_temp_c", "injection_pressure_mpa", "cooling_time_s"
    ]
    target_cols = ["tensile_strength_mpa", "volumetric_shrinkage_pct"]

    df_train = pd.read_csv(os.path.join(data_dir, "dataset_train.csv"))
    df_test = pd.read_csv(os.path.join(data_dir, "dataset_test_id.csv"))

    surrogate = joblib.load(os.path.join(base_dir, "models", "surrogate_randomforest.joblib"))

    # ─── Ablation Study ──────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("1. FEATURE ABLATION STUDY (Random Forest, ID Test Set N=750)")
    print("=" * 80)
    ablation_results = run_feature_ablation(df_train, df_test, feature_cols, target_cols)

    abl_headers = ["Ablated Feature", "Tensile R2", "Shrink R2", "Tensile R2 Drop", "Shrink R2 Drop"]
    abl_rows = []
    for r in ablation_results:
        r2_drop_t = r.get("tensile_r2_drop", "-")
        r2_drop_s = r.get("shrinkage_r2_drop", "-")
        abl_rows.append([
            r["ablated_feature"],
            f"{r['tensile_r2']:.4f}",
            f"{r['shrinkage_r2']:.4f}",
            f"{r2_drop_t:.4f}" if r2_drop_t != "-" else "-",
            f"{r2_drop_s:.4f}" if r2_drop_s != "-" else "-"
        ])
    print(format_table(abl_rows, abl_headers))

    # ─── Noise Robustness ────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("2. SENSOR NOISE ROBUSTNESS STUDY (Additive Gaussian on all Features)")
    print("=" * 80)
    noise_results = run_noise_robustness(
        df_train, df_test, feature_cols, target_cols,
        noise_levels=[0.0, 0.05, 0.10, 0.15, 0.20, 0.30]
    )

    noise_headers = ["Noise Level", "Tensile MAE", "Tensile R2", "Shrink MAE", "Shrink R2"]
    noise_rows = []
    for r in noise_results:
        noise_rows.append([
            r["noise_pct"],
            f"{r['tensile_mae']:.4f}",
            f"{r['tensile_r2']:.4f}",
            f"{r['shrinkage_mae']:.4f}",
            f"{r['shrinkage_r2']:.4f}"
        ])
    print(format_table(noise_rows, noise_headers))

    # ─── Weight Sensitivity ──────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("3. OBJECTIVE WEIGHT SENSITIVITY (Realized via True Simulator, N=100 nominal samples)")
    print("=" * 80)

    df_nominal = df_test.head(100).copy()

    # Precompute candidate grid (same as AdaptiveProcessTuner)
    t_vals = np.linspace(205.0, 255.0, 7)
    p_vals = np.linspace(65.0, 145.0, 7)
    c_vals = np.linspace(12.0, 32.0, 5)
    grid_T, grid_P, grid_C = np.meshgrid(t_vals, p_vals, c_vals, indexing="ij")
    actuator_candidates = np.column_stack([grid_T.ravel(), grid_P.ravel(), grid_C.ravel()])

    weight_results = run_weight_sensitivity(
        df_nominal, surrogate,
        target_tensile=52.0, spec_S=(49.0, 55.0),
        target_shrink=1.20, spec_V=(0.80, 1.60),
        energy_norm=3.15,
        actuator_candidates=actuator_candidates,
        bounds={},
        sop_defaults={"melt_temp_c": 230.0, "injection_pressure_mpa": 100.0, "cooling_time_s": 20.0}
    )

    weight_headers = ["Weight Config", "Yield %", "Mean Energy (kWh)", "Mean T_melt (°C)", "Mean P_inj (MPa)", "Mean t_cool (s)"]
    weight_rows = []
    for r in weight_results:
        weight_rows.append([
            r["config"],
            f"{r['mean_yield_pct']:.1f}%",
            f"{r['mean_energy_kwh']:.3f}",
            f"{r['mean_T_melt']:.1f}",
            f"{r['mean_P_inj']:.1f}",
            f"{r['mean_t_cool']:.1f}"
        ])
    print(format_table(weight_rows, weight_headers))

    all_results = {
        "ablation": ablation_results,
        "noise_robustness": noise_results,
        "weight_sensitivity": weight_results
    }

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved ablation results to: {results_path}")
    print("\n" + "=" * 80)
    print("Gate 4 Ablation & Robustness Experiment Complete.")
    print("=" * 80)


if __name__ == "__main__":
    main()
