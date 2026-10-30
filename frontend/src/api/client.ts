import type {
  MaterialInputs,
  ProcessParameters,
  QualityOutcomes,
  DomainGuardResult,
  TuningRecommendation
} from './types';

// Future FastAPI base URL (configurable via Vite env)
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const NOMINAL_SOP: ProcessParameters = {
  melt_temp_c: 230.0,
  injection_pressure_mpa: 100.0,
  cooling_time_s: 20.0
};

export const MACHINE_HARD_BOUNDS = {
  melt_temp_c: { min: 205.0, max: 255.0, units: '°C' },
  injection_pressure_mpa: { min: 65.0, max: 145.0, units: 'MPa' },
  cooling_time_s: { min: 12.0, max: 32.0, units: 's' }
};

export const SUPPORTED_INPUT_BOUNDS = {
  moisture_pct: { min: 0.05, max: 0.50, units: 'wt %', nominal: 0.15 },
  melt_flow_index: { min: 14.0, max: 30.0, units: 'g/10 min', nominal: 22.0 },
  ambient_temp_c: { min: 16.0, max: 32.0, units: '°C', nominal: 24.0 },
  recycled_pct: { min: 10.0, max: 40.0, units: 'wt %', nominal: 25.0 }
};

export const QUALITY_TOLERANCES = {
  tensile: { min: 49.0, max: 55.0, target: 52.0, units: 'MPa' },
  shrinkage: { min: 0.80, max: 1.60, target: 1.20, units: '%' },
  nominal_energy: 2.458 // kWh/cycle nominal SOP
};

/**
 * Domain Guard implementation matching src/optimization/domain_guard.py.
 */
export function evaluateDomainGuard(inputs: MaterialInputs): DomainGuardResult {
  const violating: string[] = [];

  // Check physical limits
  if (inputs.moisture_pct < 0.0) violating.push('moisture cannot be negative');
  if (inputs.melt_flow_index <= 0.0) violating.push('MFI must be positive');
  if (inputs.recycled_pct < 0.0 || inputs.recycled_pct > 100.0) violating.push('recycled content out of [0, 100]%');

  if (violating.length > 0) {
    return {
      is_valid: false,
      status: 'INVALID_INPUT',
      rejection_reason: violating.join('; '),
      violating_fields: violating
    };
  }

  // Extreme uncompensable moisture
  if (inputs.moisture_pct > 0.55) {
    return {
      is_valid: false,
      status: 'UNCOMPENSABLE',
      rejection_reason: `Moisture ${inputs.moisture_pct.toFixed(2)} wt % exceeds maximum compensable threshold (0.55 wt %). Feasible set is empty.`,
      violating_fields: ['moisture_pct']
    };
  }

  // Out-of-distribution training support checks
  const out_bounds: string[] = [];
  if (inputs.moisture_pct < SUPPORTED_INPUT_BOUNDS.moisture_pct.min || inputs.moisture_pct > SUPPORTED_INPUT_BOUNDS.moisture_pct.max) {
    out_bounds.push(`moisture_pct=${inputs.moisture_pct.toFixed(2)} outside [${SUPPORTED_INPUT_BOUNDS.moisture_pct.min}, ${SUPPORTED_INPUT_BOUNDS.moisture_pct.max}]`);
  }
  if (inputs.melt_flow_index < SUPPORTED_INPUT_BOUNDS.melt_flow_index.min || inputs.melt_flow_index > SUPPORTED_INPUT_BOUNDS.melt_flow_index.max) {
    out_bounds.push(`MFI=${inputs.melt_flow_index.toFixed(1)} outside [${SUPPORTED_INPUT_BOUNDS.melt_flow_index.min}, ${SUPPORTED_INPUT_BOUNDS.melt_flow_index.max}]`);
  }
  if (inputs.ambient_temp_c < SUPPORTED_INPUT_BOUNDS.ambient_temp_c.min || inputs.ambient_temp_c > SUPPORTED_INPUT_BOUNDS.ambient_temp_c.max) {
    out_bounds.push(`ambient_temp_c=${inputs.ambient_temp_c.toFixed(1)} outside [${SUPPORTED_INPUT_BOUNDS.ambient_temp_c.min}, ${SUPPORTED_INPUT_BOUNDS.ambient_temp_c.max}]`);
  }
  if (inputs.recycled_pct < SUPPORTED_INPUT_BOUNDS.recycled_pct.min || inputs.recycled_pct > SUPPORTED_INPUT_BOUNDS.recycled_pct.max) {
    out_bounds.push(`recycled_pct=${inputs.recycled_pct.toFixed(1)} outside [${SUPPORTED_INPUT_BOUNDS.recycled_pct.min}, ${SUPPORTED_INPUT_BOUNDS.recycled_pct.max}]`);
  }

  if (out_bounds.length > 0) {
    return {
      is_valid: false,
      status: 'OOD_REJECTED',
      rejection_reason: `Rejected by Domain Guard: ${out_bounds.join(', ')}. Outside validated surrogate support envelope.`,
      violating_fields: out_bounds
    };
  }

  return {
    is_valid: true,
    status: 'VALID',
    rejection_reason: null,
    violating_fields: []
  };
}

/**
 * Authoritative physical simulator computation matching PolymerInjectionSimulator.
 */
export function simulateCycle(
  inputs: MaterialInputs,
  params: ProcessParameters,
  addNoise: boolean = false
): QualityOutcomes {
  // Tensile strength S (MPa)
  const delta_T = params.melt_temp_c - 230.0;
  const term_therm = 0.06 * delta_T - 0.0035 * (delta_T ** 2);
  const term_press = 4.50 * Math.log(params.injection_pressure_mpa / 100.0);
  const term_moist = 14.0 * Math.pow(inputs.moisture_pct, 1.40);
  const cooling_deficit = (params.cooling_time_s - 20.0) / 20.0;
  const term_cool = params.cooling_time_s < 20.0 ? 2.50 * (cooling_deficit ** 2) : 0.0;
  const term_rec = 0.08 * (inputs.recycled_pct - 25.0);
  const term_int = 1.80 * (delta_T / 25.0) * ((22.0 - inputs.melt_flow_index) / 8.0);
  const noise_S = addNoise ? (Math.random() - 0.5) * 0.35 * 2 : 0.0;

  const S = 53.5 + term_therm + term_press - term_moist - term_cool - term_rec + term_int + noise_S;

  // Volumetric shrinkage V_sh (%)
  const term_sh_T = 0.008 * delta_T;
  const term_sh_P = 0.45 * ((params.injection_pressure_mpa - 100.0) / 100.0);
  const term_sh_cool = 1.20 * Math.exp(-params.cooling_time_s / 8.0);
  const term_sh_moist = 0.60 * (inputs.moisture_pct - 0.15);
  const term_sh_rec = 0.005 * (inputs.recycled_pct - 25.0);
  const noise_V = addNoise ? (Math.random() - 0.5) * 0.035 * 2 : 0.0;

  const V_sh = 1.15 + term_sh_T - term_sh_P + term_sh_cool + term_sh_moist - term_sh_rec + noise_V;

  // Specific process energy E (kWh/cycle)
  const temp_delta_amb = Math.max(0.0, params.melt_temp_c - inputs.ambient_temp_c);
  const E = 0.20 + 0.008 * temp_delta_amb + 0.009 * params.injection_pressure_mpa + 0.030 * params.cooling_time_s;

  const tensile_in_spec = S >= QUALITY_TOLERANCES.tensile.min && S <= QUALITY_TOLERANCES.tensile.max;
  const shrinkage_in_spec = V_sh >= QUALITY_TOLERANCES.shrinkage.min && V_sh <= QUALITY_TOLERANCES.shrinkage.max;

  return {
    tensile_strength_mpa: Number(S.toFixed(3)),
    volumetric_shrinkage_pct: Number(V_sh.toFixed(3)),
    energy_kwh: Number(E.toFixed(3)),
    tensile_in_spec,
    shrinkage_in_spec,
    overall_in_spec: tensile_in_spec && shrinkage_in_spec
  };
}

/**
 * Offline Adaptive Parameter Tuner matching src/optimization/adaptive_tuner.py
 * Minimizes energy while strictly respecting padded tensile safety margin and shrinkage constraints.
 */
export function tuneParametersOffline(
  inputs: MaterialInputs,
  baseMargin: number = 1.50,
  recycledSlope: number = 0.035
): TuningRecommendation {
  const startTime = performance.now();
  const guard = evaluateDomainGuard(inputs);

  // Calculate dynamic adaptive safety margin
  const delta_recycled = Math.max(0.0, inputs.recycled_pct - 25.0);
  const safety_margin_S = baseMargin + recycledSlope * delta_recycled;
  const s_min_safe = QUALITY_TOLERANCES.tensile.min + safety_margin_S;

  if (!guard.is_valid) {
    const sopSim = simulateCycle(inputs, NOMINAL_SOP);
    return {
      status: 'OOD_REJECTED',
      parameters: NOMINAL_SOP,
      predicted_tensile_mpa: sopSim.tensile_strength_mpa,
      predicted_shrinkage_pct: sopSim.volumetric_shrinkage_pct,
      predicted_energy_kwh: sopSim.energy_kwh,
      simulated_outcomes: sopSim,
      energy_savings_pct: 0.0,
      safety_margin_S,
      guard_result: guard,
      execution_latency_ms: Number((performance.now() - startTime).toFixed(1))
    };
  }

  // Grid search over bounded actuator domain
  // Evaluates candidate parameters minimizing E subject to hard safety constraints
  const tempCandidates = [205.0, 210.0, 215.0, 220.0, 225.0, 230.0];
  const pressureCandidates = [90.0, 100.0, 110.0, 120.0, 130.0, 140.0, 144.0];
  const coolingCandidates = [12.0, 14.0, 16.0, 18.0, 20.0];

  let bestParams: ProcessParameters = NOMINAL_SOP;
  let bestEnergy = Infinity;
  let bestSim: QualityOutcomes | null = null;

  for (const T of tempCandidates) {
    for (const P of pressureCandidates) {
      for (const t of coolingCandidates) {
        const candidateParams: ProcessParameters = {
          melt_temp_c: T,
          injection_pressure_mpa: P,
          cooling_time_s: t
        };

        const sim = simulateCycle(inputs, candidateParams, false);

        // Hard constraint check including safety margin
        if (
          sim.tensile_strength_mpa >= s_min_safe &&
          sim.tensile_strength_mpa <= QUALITY_TOLERANCES.tensile.max &&
          sim.volumetric_shrinkage_pct >= QUALITY_TOLERANCES.shrinkage.min &&
          sim.volumetric_shrinkage_pct <= QUALITY_TOLERANCES.shrinkage.max
        ) {
          if (sim.energy_kwh < bestEnergy) {
            bestEnergy = sim.energy_kwh;
            bestParams = candidateParams;
            bestSim = sim;
          }
        }
      }
    }
  }

  const sopSim = simulateCycle(inputs, NOMINAL_SOP);
  const baselineEnergy = sopSim.energy_kwh;
  const executionLatency = Number((performance.now() - startTime).toFixed(1));

  if (!bestSim) {
    // If no candidate met padded safety bound, fallback to safest feasible
    return {
      status: 'INFEASIBLE',
      parameters: NOMINAL_SOP,
      predicted_tensile_mpa: sopSim.tensile_strength_mpa,
      predicted_shrinkage_pct: sopSim.volumetric_shrinkage_pct,
      predicted_energy_kwh: sopSim.energy_kwh,
      simulated_outcomes: sopSim,
      energy_savings_pct: 0.0,
      safety_margin_S,
      guard_result: guard,
      execution_latency_ms: executionLatency
    };
  }

  const savingsPct = Number((((baselineEnergy - bestEnergy) / baselineEnergy) * 100).toFixed(2));

  return {
    status: 'OPTIMAL',
    parameters: bestParams,
    predicted_tensile_mpa: bestSim.tensile_strength_mpa,
    predicted_shrinkage_pct: bestSim.volumetric_shrinkage_pct,
    predicted_energy_kwh: bestSim.energy_kwh,
    simulated_outcomes: bestSim,
    energy_savings_pct: Math.max(0.0, savingsPct),
    safety_margin_S: Number(safety_margin_S.toFixed(3)),
    guard_result: guard,
    execution_latency_ms: executionLatency
  };
}

/**
 * Unified API Client for FastAPI backend integration.
 * In development, defaults to local physics calculation while allowing seamless switch to live backend.
 */
export class OptimizationApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async checkHealth(): Promise<{ status: string; mode: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, { signal: AbortSignal.timeout(60000) });
      if (response.ok) {
        return { status: 'ONLINE', mode: 'FASTAPI_REST' };
      }
    } catch {
      // Offline fallback
    }
    return { status: 'OFFLINE_PREVIEW', mode: 'CLIENT_CALIBRATED_ENGINE' };
  }

  async tune(inputs: MaterialInputs): Promise<TuningRecommendation> {
    try {
      const response = await fetch(`${this.baseUrl}/api/tune`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(inputs),
        signal: AbortSignal.timeout(60000)
      });
      if (response.ok) {
        return await response.json();
      }
    } catch {
      // Graceful offline execution
    }
    return tuneParametersOffline(inputs);
  }
}

export const apiClient = new OptimizationApiClient();
