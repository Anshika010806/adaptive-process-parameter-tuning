import type {
  AblationRow,
  RobustnessNoiseLevel,
  SensitivityMarginPoint,
  SurrogateBenchmarkModel
} from '../api/types';

/**
 * Real research metrics sourced directly from:
 * - reports/gate1 / data/surrogate_benchmark_results.json
 * - reports/gate2/gate2_tuning_report.json
 * - reports/gate3/gate3_validation_report.json
 * - reports/gate3_corrected/gate3_corrective_comparison.md
 * - reports/gate4/gate4_ablation_summary.csv
 * - reports/gate4/gate4_summary_metrics.json
 */

export const OVERVIEW_METRICS = {
  energyReductionMeanPct: 16.32,
  energyReductionCI: [16.17, 16.47] as [number, number],
  baselineMeanEnergyKwh: 2.458,
  optimizedMeanEnergyKwh: 2.057,
  meanSavingsKwhPerCycle: 0.401,
  totalEvaluationCycles: 250,
  overallQualityCompliancePct: 100.0,
  totalDefects: 0,
  actuatorSafetyAdherencePct: 100.0,
  meanLatencyMs: 77.4,
  p95LatencyMs: 91.5,
  domainGuardRejectionRateOOD: 100.0 // Correctly rejects unsupported OOD scenarios
};

export const GATE3_EXPERIMENT_COMPARISONS = [
  {
    configuration: 'Earlier Experiment: Initial Safety Margin (0.80 MPa)',
    margin_label: '0.80 MPa (Initial)',
    total_cycles: 250,
    defects: 93,
    compliance_pct: 62.8,
    energy_reduction_pct: 17.56,
    status: 'High Defect Rate (Boundary Bias Exposed)',
    notes: 'Optimizer selected setpoints at the lower 49.0 MPa boundary, causing 37.2% defect rate under stochastic noise.'
  },
  {
    configuration: 'Earlier Experiment: Candidate Safety Margin (1.20 MPa)',
    margin_label: '1.20 MPa (Candidate)',
    total_cycles: 250,
    defects: 12,
    compliance_pct: 95.2,
    energy_reduction_pct: 16.98,
    status: 'Partially Improved (Residual High-Recycled Defects)',
    notes: 'Constant 1.20 MPa margin reduced defects but still yielded 12 defects concentrated at >32.5 wt% recycled content.'
  },
  {
    configuration: 'Corrected Configuration: Adaptive Recycled Margin',
    margin_label: '1.50 MPa + 0.035·max(0, C_rec - 25.0)',
    total_cycles: 250,
    defects: 0,
    compliance_pct: 100.0,
    energy_reduction_pct: 16.32,
    status: 'Fully Corrected & Revalidated',
    notes: 'Quadrature uncertainty decomposition + adaptive slope achieved 100% compliance across all 250 cycles with 16.32% energy reduction.'
  }
];

export const TEST_SUITE_BREAKDOWN = [
  { module: 'test_gate4_evaluation.py', tests: 30, scope: 'Ablation, noise regimes, sensitivity sweeps, actuator limits' },
  { module: 'test_simulation.py', tests: 16, scope: 'Physical simulator thermodynamics, transients, noise injection' },
  { module: 'test_gate2_tuning.py', tests: 15, scope: 'Constrained tuning engine, Domain Guard OOD rejection' },
  { module: 'test_gate2_corrective_iteration.py', tests: 12, scope: 'Adaptive margin, chance constraints, quadrature decomposition' },
  { module: 'test_gate3_validation.py', tests: 11, scope: 'Closed-loop matched validation, error analysis, confidence intervals' },
  { module: 'test_profiler.py', tests: 7, scope: 'Dataset profiling, defensive validation, category handling' },
  { module: 'test_adaptive_tuner.py', tests: 6, scope: 'Closed-loop actuator enforcement, tree surrogate optimization' },
  { module: 'test_surrogate_benchmark.py', tests: 6, scope: 'Multi-output regression, leakage checks, model serialization' },
  { module: 'test_baselines.py', tests: 5, scope: 'Static SOP controller, dummy & linear regression baselines' }
];

export const GATE1_SURROGATE_MODELS: SurrogateBenchmarkModel[] = [
  {
    model_name: 'Dummy (Mean)',
    val_mean_r2: -0.001,
    test_tensile_mae: 1.410,
    test_tensile_r2: -0.001,
    test_shrinkage_mae: 0.146,
    test_shrinkage_r2: -0.001,
    test_mean_r2: -0.001,
    ood1_feedstock_r2: -7.234,
    ood2_thermal_r2: -0.640,
    ood3_extrap_r2: -36.919,
    ood4_sensor_r2: -0.232
  },
  {
    model_name: 'Linear Regression',
    val_mean_r2: 0.847,
    test_tensile_mae: 0.674,
    test_tensile_r2: 0.759,
    test_shrinkage_mae: 0.033,
    test_shrinkage_r2: 0.946,
    test_mean_r2: 0.852,
    ood1_feedstock_r2: 0.709,
    ood2_thermal_r2: -0.746,
    ood3_extrap_r2: -0.137,
    ood4_sensor_r2: 0.151
  },
  {
    model_name: 'Ridge (alpha=10)',
    val_mean_r2: 0.847,
    test_tensile_mae: 0.674,
    test_tensile_r2: 0.759,
    test_shrinkage_mae: 0.033,
    test_shrinkage_r2: 0.946,
    test_mean_r2: 0.852,
    ood1_feedstock_r2: 0.713,
    ood2_thermal_r2: -0.742,
    ood3_extrap_r2: -0.166,
    ood4_sensor_r2: 0.152
  },
  {
    model_name: 'Decision Tree (depth=16)',
    val_mean_r2: 0.754,
    test_tensile_mae: 0.559,
    test_tensile_r2: 0.834,
    test_shrinkage_mae: 0.078,
    test_shrinkage_r2: 0.696,
    test_mean_r2: 0.765,
    ood1_feedstock_r2: -6.719,
    ood2_thermal_r2: 0.357,
    ood3_extrap_r2: -33.345,
    ood4_sensor_r2: 0.497
  },
  {
    model_name: 'Random Forest (100 trees)',
    val_mean_r2: 0.878,
    test_tensile_mae: 0.423,
    test_tensile_r2: 0.907,
    test_shrinkage_mae: 0.055,
    test_shrinkage_r2: 0.851,
    test_mean_r2: 0.879,
    ood1_feedstock_r2: -6.732,
    ood2_thermal_r2: 0.704,
    ood3_extrap_r2: -33.585,
    ood4_sensor_r2: 0.675
  }
];

export const GATE4_ABLATION_VARIANTS: AblationRow[] = [
  {
    variant_id: 'full_corrected',
    variant_name: 'Full Corrected Tuner',
    total_cycles: 250,
    optimizer_feasible_pct: 100.0,
    tensile_compliance_pct: 100.0,
    shrinkage_compliance_pct: 100.0,
    overall_compliance_pct: 100.0,
    total_defects: 0,
    mean_energy_kwh: 2.057,
    energy_reduction_pct_mean: 16.32,
    energy_reduction_ci_lower: 16.17,
    energy_reduction_ci_upper: 16.47,
    mean_sim_tensile_mpa: 50.17,
    min_sim_tensile_mpa: 49.02,
    latency_mean_ms: 77.4,
    actuator_limits_respected: true
  },
  {
    variant_id: 'no_recycled_protection',
    variant_name: 'Ablation A: No Recycled Protection',
    total_cycles: 250,
    optimizer_feasible_pct: 100.0,
    tensile_compliance_pct: 99.2,
    shrinkage_compliance_pct: 100.0,
    overall_compliance_pct: 99.2,
    total_defects: 2,
    mean_energy_kwh: 2.053,
    energy_reduction_pct_mean: 16.47,
    energy_reduction_ci_lower: 16.34,
    energy_reduction_ci_upper: 16.61,
    mean_sim_tensile_mpa: 50.09,
    min_sim_tensile_mpa: 48.83,
    latency_mean_ms: 72.3,
    actuator_limits_respected: true
  },
  {
    variant_id: 'initial_baseline_margin',
    variant_name: 'Ablation B: Initial Baseline Margin (0.80 MPa)',
    total_cycles: 250,
    optimizer_feasible_pct: 100.0,
    tensile_compliance_pct: 78.8,
    shrinkage_compliance_pct: 100.0,
    overall_compliance_pct: 78.8,
    total_defects: 53,
    mean_energy_kwh: 2.031,
    energy_reduction_pct_mean: 17.38,
    energy_reduction_ci_lower: 17.29,
    energy_reduction_ci_upper: 17.48,
    mean_sim_tensile_mpa: 49.35,
    min_sim_tensile_mpa: 47.74,
    latency_mean_ms: 70.3,
    actuator_limits_respected: true
  },
  {
    variant_id: 'candidate_margin_120',
    variant_name: 'Ablation C: Candidate Margin (1.20 MPa)',
    total_cycles: 250,
    optimizer_feasible_pct: 100.0,
    tensile_compliance_pct: 95.2,
    shrinkage_compliance_pct: 100.0,
    overall_compliance_pct: 95.2,
    total_defects: 12,
    mean_energy_kwh: 2.041,
    energy_reduction_pct_mean: 16.98,
    energy_reduction_ci_lower: 16.86,
    energy_reduction_ci_upper: 17.11,
    mean_sim_tensile_mpa: 49.79,
    min_sim_tensile_mpa: 48.24,
    latency_mean_ms: 73.5,
    actuator_limits_respected: true
  },
  {
    variant_id: 'unpadded_zero_margin',
    variant_name: 'Ablation D: Unpadded (0.00 MPa Margin)',
    total_cycles: 250,
    optimizer_feasible_pct: 100.0,
    tensile_compliance_pct: 18.4,
    shrinkage_compliance_pct: 100.0,
    overall_compliance_pct: 18.4,
    total_defects: 204,
    mean_energy_kwh: 2.021,
    energy_reduction_pct_mean: 17.80,
    energy_reduction_ci_lower: 17.76,
    energy_reduction_ci_upper: 17.84,
    mean_sim_tensile_mpa: 48.59,
    min_sim_tensile_mpa: 47.26,
    latency_mean_ms: 70.4,
    actuator_limits_respected: true
  },
  {
    variant_id: 'static_sop',
    variant_name: 'Reference: Static SOP Baseline',
    total_cycles: 250,
    optimizer_feasible_pct: 100.0,
    tensile_compliance_pct: 100.0,
    shrinkage_compliance_pct: 100.0,
    overall_compliance_pct: 100.0,
    total_defects: 0,
    mean_energy_kwh: 2.458,
    energy_reduction_pct_mean: 0.0,
    energy_reduction_ci_lower: 0.0,
    energy_reduction_ci_upper: 0.0,
    mean_sim_tensile_mpa: 52.45,
    min_sim_tensile_mpa: 50.52,
    latency_mean_ms: 0.0,
    actuator_limits_respected: true
  }
];

export const NOISE_ROBUSTNESS_DATA: RobustnessNoiseLevel[] = [
  {
    noise_sigma: 0.0,
    cycles: 250,
    overall_compliance_pct: 100.0,
    quality_defects: 0,
    energy_reduction_pct: 16.32,
    min_tensile_mpa: 49.56
  },
  {
    noise_sigma: 0.35,
    cycles: 250,
    overall_compliance_pct: 100.0,
    quality_defects: 0,
    energy_reduction_pct: 16.32,
    min_tensile_mpa: 49.02
  },
  {
    noise_sigma: 0.50,
    cycles: 250,
    overall_compliance_pct: 98.4,
    quality_defects: 4,
    energy_reduction_pct: 16.32,
    min_tensile_mpa: 48.70
  }
];

export const SENSITIVITY_MARGIN_SWEEP: SensitivityMarginPoint[] = [
  { margin_mpa: 0.00, cycles: 250, tensile_compliance_pct: 18.4, overall_compliance_pct: 18.4, quality_defects: 204, energy_reduction_pct: 17.80, mean_tensile_mpa: 48.59, min_tensile_mpa: 47.26 },
  { margin_mpa: 0.40, cycles: 250, tensile_compliance_pct: 47.6, overall_compliance_pct: 47.6, quality_defects: 131, energy_reduction_pct: 17.61, mean_tensile_mpa: 48.93, min_tensile_mpa: 47.46 },
  { margin_mpa: 0.80, cycles: 250, tensile_compliance_pct: 78.8, overall_compliance_pct: 78.8, quality_defects: 53, energy_reduction_pct: 17.38, mean_tensile_mpa: 49.35, min_tensile_mpa: 47.74 },
  { margin_mpa: 1.20, cycles: 250, tensile_compliance_pct: 95.2, overall_compliance_pct: 95.2, quality_defects: 12, energy_reduction_pct: 16.98, mean_tensile_mpa: 49.79, min_tensile_mpa: 48.24 },
  { margin_mpa: 1.50, cycles: 250, tensile_compliance_pct: 99.2, overall_compliance_pct: 99.2, quality_defects: 2, energy_reduction_pct: 16.47, mean_tensile_mpa: 50.09, min_tensile_mpa: 48.83 },
  { margin_mpa: 1.80, cycles: 250, tensile_compliance_pct: 99.6, overall_compliance_pct: 99.6, quality_defects: 1, energy_reduction_pct: 16.25, mean_tensile_mpa: 50.38, min_tensile_mpa: 48.98 },
  { margin_mpa: 2.20, cycles: 250, tensile_compliance_pct: 100.0, overall_compliance_pct: 100.0, quality_defects: 0, energy_reduction_pct: 15.45, mean_tensile_mpa: 50.81, min_tensile_mpa: 49.70 }
];

export const RECYCLED_CONTENT_SWEEP = [
  { recycled_wt_pct: 10.0, full_corrected_compliance: 100.0, unpadded_compliance: 90.0, energy_red: 17.76 },
  { recycled_wt_pct: 15.0, full_corrected_compliance: 100.0, unpadded_compliance: 40.0, energy_red: 17.76 },
  { recycled_wt_pct: 20.0, full_corrected_compliance: 100.0, unpadded_compliance: 30.0, energy_red: 16.23 },
  { recycled_wt_pct: 25.0, full_corrected_compliance: 100.0, unpadded_compliance: 20.0, energy_red: 16.57 },
  { recycled_wt_pct: 30.0, full_corrected_compliance: 100.0, unpadded_compliance: 10.0, energy_red: 15.40 },
  { recycled_wt_pct: 35.0, full_corrected_compliance: 100.0, unpadded_compliance: 0.0, energy_red: 14.98 },
  { recycled_wt_pct: 40.0, full_corrected_compliance: 100.0, unpadded_compliance: 0.0, energy_red: 14.58 }
];
