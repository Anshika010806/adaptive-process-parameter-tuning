"""
Experiment Execution: Comparative Surrogate Benchmarking.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 1)
"""

import os
import sys
import json

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.surrogate_benchmark import SurrogateBenchmark


def format_table(rows, headers):
    """Simple ASCII table formatter."""
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


def main():
    print("=" * 80)
    print("Worklet No. 28 - PBL-II Milestone: Comparative Surrogate Benchmarking")
    print("=" * 80)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data", "synthetic")
    models_dir = os.path.join(base_dir, "models")
    results_path = os.path.join(base_dir, "data", "surrogate_benchmark_results.json")

    benchmarker = SurrogateBenchmark(random_state=42)
    print("\nRunning model training, hyperparameter tuning on validation fold, and evaluation...")
    benchmark_payload = benchmarker.run_full_benchmark(data_dir=data_dir)

    # 1. Print Tuning Summary
    print("\n" + "=" * 80)
    print("1. HYPERPARAMETER TUNING SUMMARY (Selected on Validation Set, N=750)")
    print("=" * 80)
    for model_name, record in benchmark_payload["tuning_summary"].items():
        print(f"  - Model: {model_name:<16} | Best Params: {record['best_param']} | Val Mean R²: {record['best_val_mean_r2']:.4f}")

    # 2. Print In-Distribution Held-Out Test Set Performance
    print("\n" + "=" * 80)
    print("2. HELD-OUT IN-DISTRIBUTION TEST SET RESULTS (N=750)")
    print("=" * 80)
    id_headers = [
        "Model", "Tensile MAE", "Tensile RMSE", "Tensile R²",
        "Shrink MAE", "Shrink RMSE", "Shrink R²", "Mean R²", "Latency (ms)"
    ]
    id_rows = []
    for res in benchmark_payload["id_test_benchmarks"]:
        id_rows.append([
            res["model_name"],
            f"{res['tensile_mae']:.4f}",
            f"{res['tensile_rmse']:.4f}",
            f"{res['tensile_r2']:.4f}",
            f"{res['shrinkage_mae']:.4f}",
            f"{res['shrinkage_rmse']:.4f}",
            f"{res['shrinkage_r2']:.4f}",
            f"{res['mean_r2']:.4f}",
            f"{res['inference_latency_ms']:.4f}"
        ])
    print(format_table(id_rows, id_headers))

    # 3. Print Out-of-Distribution Stress Sets Performance
    print("\n" + "=" * 80)
    print("3. OUT-OF-DISTRIBUTION (OOD) GENERALIZATION BENCHMARKS (N=500 each)")
    print("=" * 80)
    ood_labels = {
        "ood_1_feedstock": "OOD-1: Feedstock Quality Shift (Degraded Recycled Lot)",
        "ood_2_thermal": "OOD-2: Thermal Ambient Shift (Extreme Shop-Floor Heatwave)",
        "ood_3_extrap": "OOD-3: Extrapolation Beyond Support (Moisture > 0.55 wt%)",
        "ood_4_sensor": "OOD-4: Sensor Noise / Corrupted Measurements (15% Noise)"
    }

    for ood_key, label in ood_labels.items():
        print(f"\n>>> {label}")
        rows = []
        for res in benchmark_payload["ood_benchmarks"][ood_key]:
            rows.append([
                res["model_name"],
                f"{res['tensile_mae']:.4f}",
                f"{res['tensile_rmse']:.4f}",
                f"{res['tensile_r2']:.4f}",
                f"{res['shrinkage_mae']:.4f}",
                f"{res['shrinkage_rmse']:.4f}",
                f"{res['shrinkage_r2']:.4f}",
                f"{res['mean_r2']:.4f}"
            ])
        ood_headers = ["Model", "Tensile MAE", "Tensile RMSE", "Tensile R²", "Shrink MAE", "Shrink RMSE", "Shrink R²", "Mean R²"]
        print(format_table(rows, ood_headers))

    # Save artifacts
    print("\n" + "=" * 80)
    print("4. ARTIFACT PERSISTENCE")
    print("=" * 80)
    saved_paths = benchmarker.save_models(models_dir)
    for name, path in saved_paths.items():
        print(f"  - Serialized pipeline: {os.path.basename(path)}")

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_payload, f, indent=2)
    print(f"  - Saved benchmark results payload to: {results_path}")

    print("\n" + "=" * 80)
    print("Gate 1 Benchmark Execution Complete.")
    print("=" * 80)


if __name__ == "__main__":
    main()
