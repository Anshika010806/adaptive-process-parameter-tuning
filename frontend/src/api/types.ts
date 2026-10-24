/**
 * Domain types for AI-Based Adaptive Process Parameter Tuning.
 * Corresponds to Python dataclasses and schemas in src/simulation, src/optimization, and src/validation.
 */

export interface MaterialInputs {
  moisture_pct: number;       // M in wt % [0.05, 0.50]
  melt_flow_index: number;    // MFI in g/10 min [14.0, 30.0]
  ambient_temp_c: number;     // T_amb in deg C [16.0, 32.0]
  recycled_pct: number;       // C_rec in wt % [10.0, 40.0]
}

export interface ProcessParameters {
  melt_temp_c: number;           // T_melt in deg C [205.0, 255.0]
  injection_pressure_mpa: number;// P_inj in MPa [65.0, 145.0]
  cooling_time_s: number;        // t_cool in s [12.0, 32.0]
}

export interface QualityOutcomes {
  tensile_strength_mpa: number;     // S in MPa, target: 52.0, spec: [49.0, 55.0]
  volumetric_shrinkage_pct: number; // V_sh in %, target: 1.20, spec: [0.80, 1.60]
  energy_kwh: number;               // E_proc in kWh/cycle, target: minimize
  tensile_in_spec: boolean;
  shrinkage_in_spec: boolean;
  overall_in_spec: boolean;
}

export interface DomainGuardResult {
  is_valid: boolean;
  status: 'VALID' | 'OOD_REJECTED' | 'INVALID_INPUT' | 'UNCOMPENSABLE';
  rejection_reason: string | null;
  violating_fields: string[];
}

export interface TuningRecommendation {
  status: 'OPTIMAL' | 'OOD_REJECTED' | 'INFEASIBLE';
  parameters: ProcessParameters;
  predicted_tensile_mpa: number;
  predicted_shrinkage_pct: number;
  predicted_energy_kwh: number;
  simulated_outcomes?: QualityOutcomes;
  energy_savings_pct: number;
  safety_margin_S: number;
  guard_result: DomainGuardResult;
  execution_latency_ms: number;
}

export interface AblationRow {
  variant_id: string;
  variant_name: string;
  total_cycles: number;
  optimizer_feasible_pct: number;
  tensile_compliance_pct: number;
  shrinkage_compliance_pct: number;
  overall_compliance_pct: number;
  total_defects: number;
  mean_energy_kwh: number;
  energy_reduction_pct_mean: number;
  energy_reduction_ci_lower: number;
  energy_reduction_ci_upper: number;
  mean_sim_tensile_mpa: number;
  min_sim_tensile_mpa: number;
  latency_mean_ms: number;
  actuator_limits_respected: boolean;
}

export interface RobustnessNoiseLevel {
  noise_sigma: number;
  cycles: number;
  overall_compliance_pct: number;
  quality_defects: number;
  energy_reduction_pct: number;
  min_tensile_mpa: number;
}

export interface SensitivityMarginPoint {
  margin_mpa: number;
  cycles: number;
  tensile_compliance_pct: number;
  overall_compliance_pct: number;
  quality_defects: number;
  energy_reduction_pct: number;
  mean_tensile_mpa: number;
  min_tensile_mpa: number;
}

export interface SurrogateBenchmarkModel {
  model_name: string;
  val_mean_r2: number;
  test_tensile_mae: number;
  test_tensile_r2: number;
  test_shrinkage_mae: number;
  test_shrinkage_r2: number;
  test_mean_r2: number;
  ood1_feedstock_r2: number;
  ood2_thermal_r2: number;
  ood3_extrap_r2: number;
  ood4_sensor_r2: number;
}
