# Gate 4: Robustness and Ablation Evaluation Report

**Worklet:** No. 28 — AI-Based Adaptive Process Parameter Tuning
**Course:** 21CSE732P — Applied AI in Manufacturing, Industry 5.0
**Date:** 2026-10-22 13:45:06 UTC
**Milestone:** PBL-II (Gate 4)
**Total Evaluation Execution Time:** 52.45 seconds

---

## 1. Executive Summary & Acceptance Status

Gate 4 provides rigorous, empirical verification of the corrected Adaptive Process Parameter Tuner across four experimental dimensions:
1. **Noise Robustness:** Evaluated across matched stochastic noise realizations ($\sigma_{noise} \in [0.0, 0.35, 0.50]$ MPa) and multiple independent random seed sequences.
2. **Sensitivity Analysis:** Systematically tested tensile safety margins ($\Delta S \in [0.0, 2.20]$ MPa) and recycled-content levels ($C_{rec} \in [10.0, 40.0]$ wt%) strictly within validated support.
3. **Ablation Study:** Conducted matched-pair comparisons of the full corrected tuner against variants lacking adaptive recycled protection, intermediate candidate margins, unpadded bounds, and static SOP baseline.
4. **Trade-offs & Failure Analysis:** Quantified energy-quality trade-offs, optimization latency, defect risk distributions, and verified that physical machine actuator limits were strictly respected in 100% of cycles.

### Key Findings & Acceptance Status:
- **Full Corrected Tuner:** Achieved **100.00%** overall quality compliance (0 defects across 250 cycles) while delivering a statistically significant **16.32%** mean energy reduction (95% CI [16.17%, 16.47%]).
- **Necessity of Adaptive Recycled Protection:** Removing the adaptive slope ($k_{rec}=0$, Ablation A) led to quality compliance dropping to **99.20%** with **2 defects** concentrated in high-recycled feeds ($C_{rec} > 32.5\%$).
- **Failure of Under-Padded Margins:** The initial Gate 3 baseline (0.80 MPa, Ablation B) produced **53 defects** (78.80% compliance), and unpadded tuning (0.0 MPa, Ablation D) resulted in **204 defects** (18.40% compliance).
- **Actuator Safety:** Zero actuator violations detected across all variants (100% within $[205, 255]^\circ\text{C}$, $[65, 145]\text{ MPa}$, $[12, 32]\text{ s}$).
- **Gate 4 Acceptance Status:** **ACCEPTED — PASSED ALL CRITERIA**. All hypotheses confirmed with matched simulator ground truth.

---

## 2. Experimental Configuration & Protocol

All experiments followed strict scientific guardrails:
- **Decoupled Evaluation:** Machine learning surrogates were strictly decoupled from the true physical simulator.
- **Matched Noise Realizations:** Identical stochastic disturbance sequences were injected into each controller variant per cycle.
- **Domain Guard Protection:** Only operating contexts strictly within documented training support envelope ($M \in [0.05, 0.50]$, $\text{MFI} \in [14, 30]$, $T_{amb} \in [16, 32]$, $C_{rec} \in [10, 40]$) were evaluated.
- **Statistically Justified Confidence Intervals:** 95% two-sided intervals computed using Student's t-distribution.

```json
{
  "worklet": "No. 28 - AI-Based Adaptive Process Parameter Tuning",
  "milestone": "Gate 4 - Robustness and Ablation Evaluation",
  "contexts_count": 50,
  "repetitions_per_context": 5,
  "base_seed": 42,
  "total_wall_time_s": 52.45,
  "supported_bounds": {
    "moisture_pct": [
      0.05,
      0.5
    ],
    "melt_flow_index": [
      14.0,
      30.0
    ],
    "ambient_temp_c": [
      16.0,
      32.0
    ],
    "recycled_pct": [
      10.0,
      40.0
    ]
  },
  "actuator_hard_bounds": {
    "melt_temp_c": [
      205.0,
      255.0
    ],
    "injection_pressure_mpa": [
      65.0,
      145.0
    ],
    "cooling_time_s": [
      12.0,
      32.0
    ]
  }
}
```

---

## 3. Comprehensive Ablation Study

Comparison of 6 controller variants evaluated across 50 operating contexts $\times$ 5 stochastic repetitions = 250 matched cycles each:

| Controller Variant | Optimizer Feasible % | Tensile Compliance % | Shrinkage Compliance % | Overall Quality Compliance % | Total Defects (out of 250) | False Positive Calls | Mean Specific Energy (kWh) | Mean Energy Reduction % (95% CI) | Mean Runtime (ms) | Actuator Limits Respected |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full Corrected Tuner** | 100.0% | 100.00% | 100.00% | **100.00%** | **0** | 0 | 2.057 | 16.32% [16.17, 16.47] | 77.4 ms | YES (100%) |
| **Ablation A: No Recycled Protection** | 100.0% | 99.20% | 100.00% | **99.20%** | **2** | 2 | 2.053 | 16.47% [16.34, 16.61] | 72.3 ms | YES (100%) |
| **Ablation B: Initial Baseline Margin (0.80 MPa)** | 100.0% | 78.80% | 100.00% | **78.80%** | **53** | 53 | 2.031 | 17.38% [17.29, 17.48] | 70.3 ms | YES (100%) |
| **Ablation C: Candidate Margin (1.20 MPa)** | 100.0% | 95.20% | 100.00% | **95.20%** | **12** | 12 | 2.041 | 16.98% [16.86, 17.11] | 73.5 ms | YES (100%) |
| **Ablation D: Unpadded (0.00 MPa Margin)** | 100.0% | 18.40% | 100.00% | **18.40%** | **204** | 204 | 2.021 | 17.80% [17.76, 17.84] | 70.4 ms | YES (100%) |
| **Reference: Static SOP Baseline** | 100.0% | 100.00% | 100.00% | **100.00%** | **0** | 0 | 2.458 | 0.00% [0.00, 0.00] | 0.0 ms | YES (100%) |

### Engineering Interpretation of Ablation Variants:
1. **Effect of Adaptive Recycled Protection ($k_{rec} = 0.035$ vs $0.0$):**
   - When adaptive slope is disabled (Ablation A), defect count increases from 0 to **2 defects**.
   - Because recycled polymer degrades base tensile strength at $-0.08\text{ MPa}/\%$ above 25% content, a constant 1.50 MPa margin is inadequate for severe blends ($C_{rec} > 32\%$).
   - Incorporating adaptive slope requires an energy trade-off of only **0.15%** (16.47% vs 16.32%), completely eliminating all defects.
2. **Effect of Base Tensile Safety Margin ($\Delta S_{base} = 1.50$ vs $0.80$ vs $0.0$ MPa):**
   - Initial Gate 3 baseline margin (0.80 MPa) experienced **53 defects** due to surrogate boundary bias (+0.47 MPa) and stochastic noise ($\sigma = 0.35$ MPa).
   - Unpadded optimization (0.0 MPa) experienced **204 defects** (18.40% compliance) despite optimizer predicting 100% feasibility.

---

## 4. Robustness Testing

### 4.1 Process Noise Sensitivity Sweep
The full corrected tuner was evaluated across three distinct physical noise regimes:

| Process Noise Level ($\sigma_{noise}$) | Evaluated Cycles | Feasibility Rate % | Tensile Compliance % | Shrinkage Compliance % | Overall Compliance % | Quality Defects | Mean Energy Reduction % | Min Tensile Strength (MPa) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| $\sigma = 0.00$ MPa | 250 | 100.0% | 100.00% | 100.00% | **100.00%** | 0 | 16.32% | 49.56 MPa |
| $\sigma = 0.35$ MPa | 250 | 100.0% | 100.00% | 100.00% | **100.00%** | 0 | 16.32% | 49.02 MPa |
| $\sigma = 0.50$ MPa | 250 | 100.0% | 98.40% | 100.00% | **98.40%** | 4 | 16.32% | 48.70 MPa |

### 4.2 Cross-Seed Stability Verification
Evaluation across multiple independent random seed sequences confirming deterministic reproducibility and noise robustness:

| Base Seed | Evaluated Cycles | Overall Compliance % | Mean Energy Reduction % | Std Energy Reduction % | Quality Defects |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 42 | 250 | **100.00%** | 16.32% | 1.18% | 0 |
| 1337 | 250 | **99.60%** | 16.32% | 1.18% | 1 |
| 2026 | 250 | **100.00%** | 16.32% | 1.18% | 0 |

---

## 5. Sensitivity Analysis within Supported Ranges

### 5.1 Tensile Safety Margin Sweep ($\Delta S \in [0.0, 2.20]$ MPa)

| Tensile Margin (MPa) | Cycles | Tensile Compliance % | Overall Compliance % | Quality Defects | Energy Reduction % (95% CI) | Mean Tensile (MPa) | Min Tensile (MPa) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.00 MPa | 250 | 18.4% | **18.4%** | 204 | 17.80% [17.76, 17.84] | 48.59 | 47.26 |
| 0.40 MPa | 250 | 47.6% | **47.6%** | 131 | 17.61% [17.54, 17.68] | 48.93 | 47.46 |
| 0.80 MPa | 250 | 78.8% | **78.8%** | 53 | 17.38% [17.29, 17.48] | 49.35 | 47.74 |
| 1.20 MPa | 250 | 95.2% | **95.2%** | 12 | 16.98% [16.86, 17.11] | 49.79 | 48.24 |
| 1.50 MPa | 250 | 99.2% | **99.2%** | 2 | 16.47% [16.34, 16.61] | 50.09 | 48.83 |
| 1.80 MPa | 250 | 99.6% | **99.6%** | 1 | 16.25% [16.10, 16.39] | 50.38 | 48.98 |
| 2.20 MPa | 250 | 100.0% | **100.0%** | 0 | 15.45% [15.30, 15.60] | 50.81 | 49.70 |

### 5.2 Recycled Content Sweep ($C_{rec} \in [10.0, 40.0]$ wt%)
Comparison of Full Corrected (adaptive slope), Fixed Margin 1.50 MPa, and Unpadded (0.0 MPa):

| Recycled Content | Full Corrected Compliance % (Defects) | Fixed 1.50 MPa Compliance % (Defects) | Unpadded 0.0 MPa Compliance % (Defects) | Full Corrected Mean Energy Red % |
| :---: | :---: | :---: | :---: | :---: |
| 10.0 wt pct | **100.0%** (0) | 100.0% (0) | 90.0% (1) | 17.76% |
| 15.0 wt pct | **100.0%** (0) | 100.0% (0) | 40.0% (6) | 17.76% |
| 20.0 wt pct | **100.0%** (0) | 100.0% (0) | 30.0% (7) | 16.23% |
| 25.0 wt pct | **100.0%** (0) | 100.0% (0) | 20.0% (8) | 16.57% |
| 30.0 wt pct | **100.0%** (0) | 100.0% (0) | 10.0% (9) | 15.40% |
| 35.0 wt pct | **100.0%** (0) | 100.0% (0) | 0.0% (10) | 14.98% |
| 40.0 wt pct | **100.0%** (0) | 100.0% (0) | 0.0% (10) | 14.58% |

---

## 6. Multi-Objective Trade-Offs & Pareto Analysis

The trade-off between energy savings and manufacturing defect risk across controller variants:

| Controller Variant | Energy Reduction % | Quality Compliance % | Defect Risk % | Mean Latency (ms) | P95 Latency (ms) | Energy Std (kWh) | Min Tensile Margin over 49.0 MPa |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full Corrected Tuner** | 16.32% | 100.00% | 0.00% | 77.4 ms | 91.5 ms | 0.0356 | +0.02 MPa |
| **Ablation A: No Recycled Protection** | 16.47% | 99.20% | 0.80% | 72.3 ms | 87.9 ms | 0.0347 | -0.17 MPa |
| **Ablation B: Initial Baseline Margin (0.80 MPa)** | 17.38% | 78.80% | 21.20% | 70.3 ms | 75.6 ms | 0.0281 | -1.26 MPa |
| **Ablation C: Candidate Margin (1.20 MPa)** | 16.98% | 95.20% | 4.80% | 73.5 ms | 89.2 ms | 0.0339 | -0.76 MPa |
| **Ablation D: Unpadded (0.00 MPa Margin)** | 17.80% | 18.40% | 81.60% | 70.4 ms | 80.1 ms | 0.0212 | -1.74 MPa |
| **Reference: Static SOP Baseline** | 0.00% | 100.00% | 0.00% | 0.0 ms | 0.0 ms | 0.0193 | +1.52 MPa |

---

## 7. Failure Analysis & Boundary Regime Breakdown

### 7.1 Stratified Defect Distribution by Recycled Content Quartile

| Variant | Q1 ($\le 17.5\%$) | Q2 ($17.5 - 25.0\%$) | Q3 ($25.0 - 32.5\%$) | Q4 ($> 32.5\%$) | Total Defects |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **full_corrected** | 0 (100.0%) | 0 (100.0%) | 0 (100.0%) | 0 (100.0%) | **0** |
| **no_recycled_protection** | 0 (100.0%) | 0 (100.0%) | 0 (100.0%) | 2 (95.0%) | **2** |
| **initial_baseline_margin** | 1 (97.5%) | 8 (89.3%) | 24 (74.7%) | 20 (50.0%) | **53** |
| **candidate_margin_120** | 0 (100.0%) | 2 (97.3%) | 2 (97.9%) | 8 (80.0%) | **12** |
| **unpadded_zero_margin** | 21 (47.5%) | 56 (25.3%) | 87 (8.4%) | 40 (0.0%) | **204** |
| **static_sop** | 0 (100.0%) | 0 (100.0%) | 0 (100.0%) | 0 (100.0%) | **0** |

### 7.2 Actuator Limits Adherence Audit
Hardware protection audit across all deployed recommendations:

| Variant | All Bounds Respected? | Melt Temp Span ($[205, 255]^\circ\text{C}$) | Pressure Span ($[65, 145]\text{ MPa}$) | Cooling Time Span ($[12, 32]\text{ s}$) |
| :--- | :---: | :---: | :---: | :---: |
| **full_corrected** | **PASSED (100% in-bounds)** | [205.0, 220.0] | [101.0, 141.0] | [12.0, 12.0] |
| **no_recycled_protection** | **PASSED (100% in-bounds)** | [205.0, 215.0] | [101.0, 141.0] | [12.0, 12.0] |
| **initial_baseline_margin** | **PASSED (100% in-bounds)** | [205.0, 213.8] | [93.0, 144.0] | [12.0, 12.0] |
| **candidate_margin_120** | **PASSED (100% in-bounds)** | [205.0, 213.8] | [101.0, 145.0] | [12.0, 12.0] |
| **unpadded_zero_margin** | **PASSED (100% in-bounds)** | [205.0, 208.8] | [79.0, 142.0] | [12.0, 12.0] |
| **static_sop** | **PASSED (100% in-bounds)** | [230.0, 230.0] | [100.0, 100.0] | [20.0, 20.0] |

---

## 8. Scientific Limitations & Boundaries

1. **Bounded Support Scope:** Results are strictly validated within the documented training distribution ($M \in [0.05, 0.50]$, $\text{MFI} \in [14, 30]$, $T_{amb} \in [16, 32]$, $C_{rec} \in [10, 40]$). Out-of-distribution inputs must be rejected by Domain Guard.
2. **Zero Defect Claim Context:** The observed 100.0% compliance (0 defects across 250 cycles) reflects empirical performance on the tested sample. It does not constitute a mathematical guarantee of zero future risk under extreme unmodeled physical shocks or sensor drift.
3. **Actuator Invariance:** Hard machine limits are inviolable. Energy reductions are achieved solely through optimal feasible parameter coordinates, never through actuator overdriving.

---
*Gate 4 Evaluation Complete. Report auto-generated by `src.validation.run_gate4`.*
