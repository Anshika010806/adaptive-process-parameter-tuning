"""
Gate 2 Entry Point: Adaptive Process Parameter Tuning.

Course: 21CSE732P - Applied AI in Manufacturing, Industry 5.0
Worklet: No. 28 - AI-Based Adaptive Process Parameter Tuning
Milestone: PBL-II (Gate 2)

Execution:
  python -m src.optimization.run_gate2
"""

from __future__ import annotations
import os
import sys
import argparse
import json
import time
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

# Ensure repository root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.simulation.process_simulator import PolymerInjectionSimulator
from src.optimization.static_controller import StaticSOPController
from src.optimization.domain_guard import DomainGuard, GuardResult
from src.optimization.surrogate_loader import load_or_train_surrogate
from src.optimization.adaptive_tuner import AdaptiveProcessTuner, TuningRecommendation
from src.optimization.simulator_validator import SimulatorValidator, SimulatorValidationResult


def format_table(rows: List[List[Any]], headers: List[str]) -> str:
    """Format rows into a clean terminal ASCII table."""
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


def save_reports(
    report_data: Dict[str, Any],
    summary_df: pd.DataFrame,
    output_dir: str
) -> Dict[str, str]:
    """
    Save Gate 2 tuning and validation reports as JSON, CSV, and Markdown.
    """
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, "gate2_tuning_report.json")
    csv_path = os.path.join(output_dir, "gate2_tuning_summary.csv")
    md_path = os.path.join(output_dir, "gate2_tuning_report.md")

    # 1. JSON Report
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # 2. CSV Summary
    summary_df.to_csv(csv_path, index=False)

    # 3. Markdown Report
    meta = report_data["metadata"]
    opt = report_data["optimizer_configuration"]
    val = report_data["validation_results"]

    md_lines = [
        "# Gate 2 — Adaptive Process Parameter Tuning Verification Report",
        "",
        f"**Date / Timestamp:** {meta['timestamp']}  ",
        f"**Execution Mode:** {meta['execution_mode']}  ",
        f"**Surrogate Model:** {opt['surrogate_model']} (Trained on `data/synthetic/dataset_train.csv` exclusively)  ",
        f"**Search Strategy:** {opt['search_strategy']} ({opt['candidate_count']} candidate setpoints evaluated)  ",
        f"**Random Seed:** {opt['random_state']}  ",
        f"**Status:** `{val['overall_status']}`  ",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        f"- **Optimization Status:** `{val['overall_status']}`",
        f"- **Domain Guard Outcome:** `{val['domain_guard_status']}` ({val['domain_guard_message']})",
        f"- **Execution Time:** `{val['execution_time_ms']:.2f} ms`",
        ""
    ]

    if val["is_feasible"]:
        comp = val["performance_comparison"]
        md_lines.extend([
            f"- **Baseline Energy (Static SOP):** `{comp['baseline_energy_kwh']:.3f} kWh/cycle`",
            f"- **Optimized Energy (Adaptive Tuner):** `{comp['tuned_energy_kwh']:.3f} kWh/cycle`",
            f"- **Energy Savings:** `{comp['energy_reduction_kwh']:.3f} kWh/cycle` (`{comp['energy_reduction_pct']:.2f}%` reduction)",
            f"- **Simulator Quality Compliance:** Tensile `{comp['simulated_tensile_mpa']:.2f} MPa` (Spec: 49.0–55.0 MPa) | Shrinkage `{comp['simulated_shrinkage_pct']:.2f}%` (Spec: 0.80–1.60%)",
            f"- **All Hard Constraints Satisfied:** `{comp['all_specs_met']}`",
            "",
            "---",
            "",
            "## 2. Actuator Recommendation vs. Baseline SOP",
            "",
            "| Parameter | Units | Baseline SOP | Adaptive Recommendation | Machine Bounds |",
            "| :--- | :--- | :--- | :--- | :--- |",
            f"| Melt Temperature ($T_{{\\text{{melt}}}}$) | °C | {comp['baseline_melt_temp_c']:.1f} | {comp['tuned_melt_temp_c']:.1f} | [205.0, 255.0] |",
            f"| Injection Pressure ($P_{{\\text{{inj}}}}$) | MPa | {comp['baseline_injection_pressure_mpa']:.1f} | {comp['tuned_injection_pressure_mpa']:.1f} | [65.0, 145.0] |",
            f"| Cooling Dwell Time ($t_{{\\text{{cool}}}}$) | s | {comp['baseline_cooling_time_s']:.1f} | {comp['tuned_cooling_time_s']:.1f} | [12.0, 32.0] |",
            "",
            "---",
            "",
            "## 3. Surrogate Predictions vs. Authoritative Simulator Outcomes",
            "",
            "| Performance Metric | Units | Surrogate Predicted | Realized Simulator | Baseline SOP | Prediction Error | In-Spec Spec |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
            f"| Tensile Strength ($S$) | MPa | {comp['predicted_tensile_mpa']:.2f} | {comp['simulated_tensile_mpa']:.2f} | {comp['baseline_tensile_mpa']:.2f} | {comp['tensile_prediction_error']:.3f} | [49.0, 55.0] |",
            f"| Volumetric Shrinkage ($V_{{\\text{{sh}}}}$) | % | {comp['predicted_shrinkage_pct']:.3f} | {comp['simulated_shrinkage_pct']:.3f} | {comp['baseline_shrinkage_pct']:.3f} | {comp['shrinkage_prediction_error']:.3f} | [0.80, 1.60] |",
            f"| Specific Energy ($E$) | kWh/cycle | {comp['predicted_energy_kwh']:.3f} | {comp['tuned_energy_kwh']:.3f} | {comp['baseline_energy_kwh']:.3f} | {abs(comp['predicted_energy_kwh'] - comp['tuned_energy_kwh']):.3f} | Minimize |",
            ""
        ])
    else:
        md_lines.extend([
            "> [!WARNING]",
            f"> Candidate was rejected or determined infeasible: {val['rejection_reason']}",
            "",
            "No adaptive setpoint was deployed. Safe Standard Operating Procedure (SOP) fallback was retained."
        ])

    md_lines.extend([
        "---",
        "",
        "## 4. Engineering Limitations & Guardrail Discussion",
        "",
        "1. **Surrogate Generalization Hull:** Random Forest exhibits high in-distribution fidelity ($R^2 > 0.90$) but flatlines outside training support. The Domain Guard actively intercepts OOD inputs (e.g. ambient temperatures > 32 °C or moistures > 0.50 wt%) to prevent unsupported surrogate predictions.",
        "2. **Derivative-Free Grid Discretization:** The candidate search evaluates a finite bounded grid with local refinement. While ensuring zero gradient divergence on non-smooth tree surfaces, the theoretical global optimum lies in continuous space within the grid resolution.",
        "3. **Decoupled Physical Validation:** All reported improvements are independently computed using the true simulator (`PolymerInjectionSimulator`) and matched noise seeds, ensuring causal integrity before claiming manufacturing benefits.",
        ""
    ])

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    return {
        "json": json_path,
        "csv": csv_path,
        "markdown": md_path
    }


def run_gate2_single(
    moisture_pct: float,
    melt_flow_index: float,
    ambient_temp_c: float,
    recycled_pct: float,
    model_type: str = "RandomForest",
    search_strategy: str = "grid",
    candidate_budget: int = 1000,
    random_state: int = 42,
    output_dir: str = "reports/gate2",
    reject_ood: bool = True,
    add_noise: bool = False,
    safety_margin_tensile: Optional[float] = None,
    safety_margin_shrinkage: Optional[float] = None,
    recycled_margin_slope: Optional[float] = None,
    recycled_margin_threshold: Optional[float] = None,
    allow_fallback_to_strict: Optional[bool] = None,
    use_chance_constraint: bool = False,
    chance_confidence: float = 0.95
) -> Tuple[int, Dict[str, str]]:
    """Execute Gate 2 workflow for a single material disturbance context."""
    print("=" * 80)
    print("GATE 2 — ADAPTIVE PROCESS PARAMETER TUNING")
    print("Worklet No. 28 - AI-Based Adaptive Process Parameter Tuning")
    print("=" * 80)

    t_start = time.perf_counter()

    # 1. Load or train surrogate pipeline exclusively from training data
    print(f"\n[1/4] Loading surrogate model: '{model_type}'...")
    surrogate_pipe = load_or_train_surrogate(
        model_name=model_type,
        random_state=random_state
    )
    print(f"      Surrogate model loaded successfully: {surrogate_pipe.steps[-1][1].__class__.__name__}")

    # 2. Instantiate Adaptive Tuner with Domain Guard
    print(f"\n[2/4] Initializing Adaptive Process Tuner (strategy='{search_strategy}', reject_ood={reject_ood})...")
    tuner = AdaptiveProcessTuner(
        surrogate_pipeline=surrogate_pipe,
        random_state=random_state,
        search_strategy=search_strategy,
        candidate_budget=candidate_budget,
        reject_ood=reject_ood,
        refine_local=True,
        safety_margin_tensile=safety_margin_tensile,
        safety_margin_shrinkage=safety_margin_shrinkage,
        recycled_margin_slope=recycled_margin_slope,
        recycled_margin_threshold=recycled_margin_threshold,
        allow_fallback_to_strict=allow_fallback_to_strict,
        use_chance_constraint=use_chance_constraint,
        chance_confidence=chance_confidence
    )
    print(f"      Actuator candidate space precomputed: {tuner.n_candidates} candidates.")
    print(f"      Tensile safety margin: base={tuner.safety_margin_tensile:.2f} MPa, recycled_slope={tuner.recycled_margin_slope:.3f} MPa/wt%")

    # 3. Execute tuning recommendation
    print(f"\n[3/4] Evaluating material disturbance context:")
    print(f"      Moisture:            {moisture_pct:.3f} wt % (0.15 = 0.15%)")
    print(f"      Melt Flow Index:     {melt_flow_index:.2f} g/10 min")
    print(f"      Ambient Temperature: {ambient_temp_c:.1f} °C")
    print(f"      Recycled Blend:      {recycled_pct:.1f} wt %")

    rec = tuner.optimize_cycle(
        moisture_pct=moisture_pct,
        melt_flow_index=melt_flow_index,
        ambient_temp_c=ambient_temp_c,
        recycled_pct=recycled_pct
    )
    print(f"      Tuning status:       [{rec.status}] | Feasible: {rec.is_feasible}")
    print(f"      Status message:      {rec.message}")

    # 4. Independent True Simulator Validation
    print(f"\n[4/4] Validating against authoritative physical simulator (matched noise={add_noise})...")
    validator = SimulatorValidator()
    val_res = validator.validate(
        recommendation=rec,
        moisture_pct=moisture_pct,
        melt_flow_index=melt_flow_index,
        ambient_temp_c=ambient_temp_c,
        recycled_pct=recycled_pct,
        seed=random_state,
        add_noise=add_noise
    )

    t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0

    # Build reporting structures
    guard_status = rec.status if not rec.is_feasible else "VALID"
    report_dict: Dict[str, Any] = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "execution_mode": "single_cycle_evaluation",
            "milestone": "Gate 2 - Adaptive Tuning Verification",
            "worklet": "No. 28 - AI-Based Adaptive Process Parameter Tuning"
        },
        "optimizer_configuration": {
            "surrogate_model": model_type,
            "search_strategy": search_strategy,
            "candidate_count": tuner.n_candidates,
            "random_state": random_state,
            "reject_ood": reject_ood,
            "local_refinement": True,
            "machine_bounds": tuner.bounds
        },
        "material_inputs": {
            "moisture_pct": moisture_pct,
            "melt_flow_index": melt_flow_index,
            "ambient_temp_c": ambient_temp_c,
            "recycled_pct": recycled_pct
        },
        "validation_results": {
            "overall_status": rec.status,
            "is_feasible": rec.is_feasible,
            "domain_guard_status": guard_status,
            "domain_guard_message": rec.message,
            "rejection_reason": rec.message if not rec.is_feasible else None,
            "execution_time_ms": t_elapsed_ms,
            "performance_comparison": {}
        }
    }

    summary_rows = []
    if rec.is_feasible and val_res.is_feasible:
        comp_data = {
            "baseline_melt_temp_c": val_res.actuators_baseline["melt_temp_c"],
            "baseline_injection_pressure_mpa": val_res.actuators_baseline["injection_pressure_mpa"],
            "baseline_cooling_time_s": val_res.actuators_baseline["cooling_time_s"],
            "tuned_melt_temp_c": val_res.actuators_tuned["melt_temp_c"],
            "tuned_injection_pressure_mpa": val_res.actuators_tuned["injection_pressure_mpa"],
            "tuned_cooling_time_s": val_res.actuators_tuned["cooling_time_s"],
            "baseline_energy_kwh": val_res.energy_baseline_kwh,
            "tuned_energy_kwh": val_res.energy_tuned_kwh,
            "energy_reduction_kwh": val_res.energy_reduction_kwh,
            "energy_reduction_pct": val_res.energy_reduction_pct,
            "predicted_tensile_mpa": rec.predicted_tensile_mpa,
            "simulated_tensile_mpa": val_res.simulated_tuned["tensile_strength_mpa"],
            "baseline_tensile_mpa": val_res.simulated_baseline["tensile_strength_mpa"],
            "tensile_prediction_error": val_res.tensile_prediction_error,
            "predicted_shrinkage_pct": rec.predicted_shrinkage_pct,
            "simulated_shrinkage_pct": val_res.simulated_tuned["volumetric_shrinkage_pct"],
            "baseline_shrinkage_pct": val_res.simulated_baseline["volumetric_shrinkage_pct"],
            "shrinkage_prediction_error": val_res.shrinkage_prediction_error,
            "predicted_energy_kwh": rec.predicted_energy_kwh,
            "all_specs_met": val_res.realized_in_spec
        }
        report_dict["validation_results"]["performance_comparison"] = comp_data

        summary_rows.append({
            "moisture_pct": moisture_pct,
            "melt_flow_index": melt_flow_index,
            "ambient_temp_c": ambient_temp_c,
            "recycled_pct": recycled_pct,
            "status": rec.status,
            "is_feasible": True,
            "baseline_melt_temp_c": val_res.actuators_baseline["melt_temp_c"],
            "baseline_inj_press_mpa": val_res.actuators_baseline["injection_pressure_mpa"],
            "baseline_cool_time_s": val_res.actuators_baseline["cooling_time_s"],
            "tuned_melt_temp_c": val_res.actuators_tuned["melt_temp_c"],
            "tuned_inj_press_mpa": val_res.actuators_tuned["injection_pressure_mpa"],
            "tuned_cool_time_s": val_res.actuators_tuned["cooling_time_s"],
            "baseline_energy_kwh": val_res.energy_baseline_kwh,
            "tuned_energy_kwh": val_res.energy_tuned_kwh,
            "energy_saved_pct": val_res.energy_reduction_pct,
            "sim_tensile_mpa": val_res.simulated_tuned["tensile_strength_mpa"],
            "sim_shrinkage_pct": val_res.simulated_tuned["volumetric_shrinkage_pct"],
            "realized_in_spec": val_res.realized_in_spec
        })

        # Print comparison table to terminal
        print("\n" + "=" * 80)
        print("VERIFIED RESULTS: BASELINE SOP VS ADAPTIVE RECOMMENDATION")
        print("=" * 80)
        headers = ["Metric / Parameter", "Baseline SOP", "Adaptive Tuner", "Improvement / Status"]
        table_rows = [
            ["Melt Temperature (°C)", f"{val_res.actuators_baseline['melt_temp_c']:.1f}", f"{val_res.actuators_tuned['melt_temp_c']:.1f}", "Dynamic Actuation"],
            ["Injection Pressure (MPa)", f"{val_res.actuators_baseline['injection_pressure_mpa']:.1f}", f"{val_res.actuators_tuned['injection_pressure_mpa']:.1f}", "Dynamic Actuation"],
            ["Cooling Time (s)", f"{val_res.actuators_baseline['cooling_time_s']:.1f}", f"{val_res.actuators_tuned['cooling_time_s']:.1f}", "Dwell Optimization"],
            ["Specific Energy (kWh/cycle)", f"{val_res.energy_baseline_kwh:.3f}", f"{val_res.energy_tuned_kwh:.3f}", f"-{val_res.energy_reduction_pct:.2f}% ({val_res.energy_reduction_kwh:.3f} kWh saved)"],
            ["Tensile Strength (MPa)", f"{val_res.simulated_baseline['tensile_strength_mpa']:.2f}", f"{val_res.simulated_tuned['tensile_strength_mpa']:.2f}", f"In-Spec [49, 55]: {'PASS' if val_res.tensile_spec_met else 'FAIL'}"],
            ["Volumetric Shrinkage (%)", f"{val_res.simulated_baseline['volumetric_shrinkage_pct']:.3f}", f"{val_res.simulated_tuned['volumetric_shrinkage_pct']:.3f}", f"In-Spec [0.8, 1.6]: {'PASS' if val_res.shrinkage_spec_met else 'FAIL'}"],
            ["Tensile Prediction Error", "N/A", f"{val_res.tensile_prediction_error:.3f} MPa", "Surrogate vs Simulator"],
            ["Shrinkage Prediction Error", "N/A", f"{val_res.shrinkage_prediction_error:.3f} %", "Surrogate vs Simulator"],
            ["Overall Physical Spec Met", "BASELINE", "VERIFIED", f"{'PASS' if val_res.realized_in_spec else 'FAIL'}"]
        ]
        print(format_table(table_rows, headers))
    else:
        summary_rows.append({
            "moisture_pct": moisture_pct,
            "melt_flow_index": melt_flow_index,
            "ambient_temp_c": ambient_temp_c,
            "recycled_pct": recycled_pct,
            "status": rec.status,
            "is_feasible": False,
            "baseline_energy_kwh": val_res.energy_baseline_kwh,
            "tuned_energy_kwh": np.nan,
            "energy_saved_pct": np.nan,
            "sim_tensile_mpa": np.nan,
            "sim_shrinkage_pct": np.nan,
            "realized_in_spec": False
        })
        print(f"\n[REJECTED] Material condition flagged as {rec.status}: {rec.message}")

    summary_df = pd.DataFrame(summary_rows)
    report_paths = save_reports(report_dict, summary_df, output_dir)

    print("\n" + "=" * 80)
    print("GATE 2 REPORTS GENERATED")
    print("=" * 80)
    for fmt, p in report_paths.items():
        print(f"  - [{fmt.upper():8s}] {p}")
    print(f"\nExecution finished in {t_elapsed_ms:.2f} ms.")
    print("=" * 80)

    return 0, report_paths


def run_gate2_batch(
    input_file: str,
    model_type: str = "RandomForest",
    search_strategy: str = "grid",
    candidate_budget: int = 1000,
    random_state: int = 42,
    output_dir: str = "reports/gate2",
    reject_ood: bool = True,
    add_noise: bool = False,
    safety_margin_tensile: Optional[float] = None,
    safety_margin_shrinkage: Optional[float] = None,
    recycled_margin_slope: Optional[float] = None,
    recycled_margin_threshold: Optional[float] = None,
    allow_fallback_to_strict: Optional[bool] = None,
    use_chance_constraint: bool = False,
    chance_confidence: float = 0.95
) -> Tuple[int, Dict[str, str]]:
    """Execute Gate 2 workflow for a batch CSV file of material disturbance cycles."""
    print("=" * 80)
    print("GATE 2 — BATCH ADAPTIVE PROCESS PARAMETER TUNING")
    print(f"Input file: {input_file}")
    print("=" * 80)

    t_start = time.perf_counter()
    df_mat = pd.read_csv(input_file)

    surrogate_pipe = load_or_train_surrogate(model_name=model_type, random_state=random_state)
    tuner = AdaptiveProcessTuner(
        surrogate_pipeline=surrogate_pipe,
        random_state=random_state,
        search_strategy=search_strategy,
        candidate_budget=candidate_budget,
        reject_ood=reject_ood,
        safety_margin_tensile=safety_margin_tensile,
        safety_margin_shrinkage=safety_margin_shrinkage,
        recycled_margin_slope=recycled_margin_slope,
        recycled_margin_threshold=recycled_margin_threshold,
        allow_fallback_to_strict=allow_fallback_to_strict,
        use_chance_constraint=use_chance_constraint,
        chance_confidence=chance_confidence
    )

    df_tuned = tuner.tune_batch(df_mat)
    validator = SimulatorValidator()

    # Validate batch against simulator
    N = len(df_tuned)
    base_energies, tuned_energies = [], []
    sim_tensiles, sim_shrinkages = [], []
    in_spec_flags = []

    for i in range(N):
        row = df_tuned.iloc[i]
        rec = TuningRecommendation(
            melt_temp_c=float(row["melt_temp_c"]),
            injection_pressure_mpa=float(row["injection_pressure_mpa"]),
            cooling_time_s=float(row["cooling_time_s"]),
            predicted_tensile_mpa=float(row["predicted_tensile_mpa"]),
            predicted_shrinkage_pct=float(row["predicted_shrinkage_pct"]),
            predicted_energy_kwh=float(row["predicted_energy_kwh"]),
            predicted_in_spec=bool(row["predicted_in_spec"]),
            is_feasible=bool(row["is_feasible"]),
            status=str(row["status"]),
            message=str(row["message"])
        )
        val = validator.validate(
            recommendation=rec,
            moisture_pct=float(row["moisture_pct"]),
            melt_flow_index=float(row["melt_flow_index"]),
            ambient_temp_c=float(row["ambient_temp_c"]),
            recycled_pct=float(row["recycled_pct"]),
            seed=random_state + i if add_noise else None,
            add_noise=add_noise
        )
        base_energies.append(val.energy_baseline_kwh)
        tuned_energies.append(val.energy_tuned_kwh if val.is_feasible else val.energy_baseline_kwh)
        sim_tensiles.append(val.simulated_tuned["tensile_strength_mpa"] if val.is_feasible else np.nan)
        sim_shrinkages.append(val.simulated_tuned["volumetric_shrinkage_pct"] if val.is_feasible else np.nan)
        in_spec_flags.append(val.realized_in_spec if val.is_feasible else False)

    df_tuned["baseline_energy_kwh"] = base_energies
    df_tuned["realized_energy_kwh"] = tuned_energies
    df_tuned["realized_tensile_mpa"] = sim_tensiles
    df_tuned["realized_shrinkage_pct"] = sim_shrinkages
    df_tuned["realized_in_spec"] = in_spec_flags

    t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0

    feas_pct = float(df_tuned["is_feasible"].mean() * 100.0)
    in_spec_pct = float(df_tuned["realized_in_spec"].mean() * 100.0)
    mean_base_e = float(np.mean(base_energies))
    mean_tuned_e = float(np.mean(tuned_energies))
    e_reduction_pct = ((mean_base_e - mean_tuned_e) / mean_base_e) * 100.0 if mean_base_e > 0 else 0.0

    report_dict = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "execution_mode": "batch_evaluation",
            "milestone": "Gate 2 - Adaptive Tuning Verification",
            "input_file": input_file,
            "n_samples": N
        },
        "optimizer_configuration": {
            "surrogate_model": model_type,
            "search_strategy": search_strategy,
            "candidate_count": tuner.n_candidates,
            "random_state": random_state,
            "reject_ood": reject_ood
        },
        "validation_results": {
            "overall_status": "COMPLETED",
            "is_feasible": feas_pct > 0,
            "feasibility_pct": feas_pct,
            "realized_in_spec_pct": in_spec_pct,
            "baseline_mean_energy_kwh": mean_base_e,
            "tuned_mean_energy_kwh": mean_tuned_e,
            "energy_reduction_pct": e_reduction_pct,
            "execution_time_ms": t_elapsed_ms
        }
    }

    report_paths = save_reports(report_dict, df_tuned, output_dir)

    print(f"\nBatch Evaluation Complete (N={N}):")
    print(f"  - Feasible Cycles:      {feas_pct:.1f}%")
    print(f"  - Realized In-Spec:     {in_spec_pct:.1f}%")
    print(f"  - Baseline Mean Energy: {mean_base_e:.3f} kWh")
    print(f"  - Tuned Mean Energy:    {mean_tuned_e:.3f} kWh ({e_reduction_pct:.2f}% reduction)")
    print(f"  - Execution Time:       {t_elapsed_ms:.1f} ms")
    print("\nReports written to:")
    for fmt, p in report_paths.items():
        print(f"  - [{fmt.upper():8s}] {p}")

    return 0, report_paths


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gate 2: Adaptive Process Parameter Tuning Engine",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Material inputs
    parser.add_argument("--moisture", type=float, default=None,
                        help="Moisture content in wt %% (e.g. 0.15 = 0.15 %%)")
    parser.add_argument("--mfi", type=float, default=None,
                        help="Melt Flow Index in g/10 min")
    parser.add_argument("--ambient-temp", type=float, default=None,
                        help="Ambient intake temperature in deg C")
    parser.add_argument("--recycled-pct", type=float, default=None,
                        help="Recycled PCR polymer blend ratio in wt %% (e.g. 25.0 = 25.0 %%)")
    parser.add_argument("--input-file", type=str, default=None,
                        help="Path to CSV file with material disturbance batch")

    # Optimizer configuration
    parser.add_argument("--model-type", type=str, default="RandomForest",
                        choices=["RandomForest", "Ridge", "DecisionTree"],
                        help="Surrogate model type")
    parser.add_argument("--strategy", type=str, default="grid",
                        choices=["grid", "sampling", "random"],
                        help="Candidate search strategy")
    parser.add_argument("--budget", type=int, default=1000,
                        help="Candidate budget for sampling search")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="reports/gate2",
                        help="Directory to save Gate 2 reports")
    parser.add_argument("--reject-ood", action="store_true", default=True,
                        help="Strictly reject out-of-distribution inputs")
    parser.add_argument("--allow-ood", dest="reject_ood", action="store_false",
                        help="Allow OOD inputs with extrapolation warning")
    parser.add_argument("--add-noise", action="store_true", default=False,
                        help="Inject stochastic sensor/physical noise in simulator")
    parser.add_argument("--tensile-margin", type=float, default=None,
                        help="Base tensile safety margin in MPa (e.g. 1.20 or 1.50)")
    parser.add_argument("--shrinkage-margin", type=float, default=None,
                        help="Volumetric shrinkage safety margin in % (e.g. 0.05)")
    parser.add_argument("--recycled-margin-slope", type=float, default=None,
                        help="Linear margin expansion slope per wt % recycled content above threshold")
    parser.add_argument("--recycled-margin-threshold", type=float, default=None,
                        help="Threshold in wt % above which recycled margin expansion applies (default 25.0)")
    parser.add_argument("--allow-fallback-to-strict", action="store_true", default=False,
                        help="Allow fallback to raw spec boundaries when margin is unreachable")
    parser.add_argument("--use-chance-constraint", action="store_true", default=False,
                        help="Use statistically justified chance constraint based on calibrated bias and composite noise")
    parser.add_argument("--chance-confidence", type=float, default=0.95,
                        help="Confidence level for chance constraint (e.g. 0.95 or 0.99)")

    args = parser.parse_args()

    # Determine execution mode
    if args.input_file:
        exit_code, _ = run_gate2_batch(
            input_file=args.input_file,
            model_type=args.model_type,
            search_strategy=args.strategy,
            candidate_budget=args.budget,
            random_state=args.seed,
            output_dir=args.output_dir,
            reject_ood=args.reject_ood,
            add_noise=args.add_noise,
            safety_margin_tensile=args.tensile_margin,
            safety_margin_shrinkage=args.shrinkage_margin,
            recycled_margin_slope=args.recycled_margin_slope,
            recycled_margin_threshold=args.recycled_margin_threshold,
            allow_fallback_to_strict=args.allow_fallback_to_strict,
            use_chance_constraint=args.use_chance_constraint,
            chance_confidence=args.chance_confidence
        )
        return exit_code

    # Single-cycle evaluation (smoke-test default if none provided)
    if all(v is None for v in [args.moisture, args.mfi, args.ambient_temp, args.recycled_pct]):
        print("[Notice] No material inputs provided. Executing default in-domain smoke-test context.")
        m = 0.18
        mfi = 21.0
        t_amb = 25.0
        rec = 28.0
    else:
        m = args.moisture if args.moisture is not None else 0.15
        mfi = args.mfi if args.mfi is not None else 22.0
        t_amb = args.ambient_temp if args.ambient_temp is not None else 24.0
        rec = args.recycled_pct if args.recycled_pct is not None else 25.0

    exit_code, _ = run_gate2_single(
        moisture_pct=m,
        melt_flow_index=mfi,
        ambient_temp_c=t_amb,
        recycled_pct=rec,
        model_type=args.model_type,
        search_strategy=args.strategy,
        candidate_budget=args.budget,
        random_state=args.seed,
        output_dir=args.output_dir,
        reject_ood=args.reject_ood,
        add_noise=args.add_noise,
        safety_margin_tensile=args.tensile_margin,
        safety_margin_shrinkage=args.shrinkage_margin,
        recycled_margin_slope=args.recycled_margin_slope,
        recycled_margin_threshold=args.recycled_margin_threshold,
        allow_fallback_to_strict=args.allow_fallback_to_strict,
        use_chance_constraint=args.use_chance_constraint,
        chance_confidence=args.chance_confidence
    )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
