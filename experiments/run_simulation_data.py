"""
Script: Generate and inspect synthetic datasets for Worklet No. 28.

Outputs:
  - data/synthetic/dataset_train.csv (N=3500)
  - data/synthetic/dataset_val.csv (N=750)
  - data/synthetic/dataset_test_id.csv (N=750)
  - data/synthetic/dataset_ood_1_feedstock.csv (N=500)
  - data/synthetic/dataset_ood_2_thermal.csv (N=500)
  - data/synthetic/dataset_ood_3_extrap.csv (N=500)
  - data/synthetic/dataset_ood_4_sensor.csv (N=500)
"""

import os
import sys

# Ensure workspace root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.simulation.data_generator import DataGenerator


def main():
    print("=" * 70)
    print("Worklet No. 28 - AI-Based Adaptive Process Parameter Tuning")
    print("Phase 1: Generating Ground-Truth Synthetic Datasets")
    print("=" * 70)

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic")
    generator = DataGenerator()
    paths = generator.generate_and_save_all(output_dir)

    print("\nDatasets successfully generated and saved:")
    for key, path in paths.items():
        size_kb = os.path.getsize(path) / 1024.0
        print(f"  - [{key:7s}] {os.path.basename(path):32s} ({size_kb:6.1f} KB)")

    print("\nSummary Validation of Datasets:")
    import pandas as pd
    for key, path in paths.items():
        df = pd.read_csv(path)
        in_spec_pct = df["in_spec_flag"].mean() * 100.0
        mean_tensile = df["tensile_strength_mpa"].mean()
        mean_shrink = df["volumetric_shrinkage_pct"].mean()
        mean_energy = df["energy_kwh"].mean()
        print(f"  [{key:7s}] N={len(df):4d} | In-Spec: {in_spec_pct:5.1f}% | "
              f"Tensile: {mean_tensile:5.2f} MPa | Shrinkage: {mean_shrink:4.2f}% | Energy: {mean_energy:4.2f} kWh")

    print("\n" + "=" * 70)
    print("Generation complete. Datasets ready for Phase 2 baseline models.")
    print("=" * 70)


if __name__ == "__main__":
    main()
