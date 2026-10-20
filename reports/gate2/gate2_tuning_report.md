# Gate 2 — Adaptive Process Parameter Tuning Verification Report

**Date / Timestamp:** 2026-10-20T08:21:36Z
**Execution Mode:** single_cycle_evaluation
**Surrogate Model:** RandomForest (Trained on `data/synthetic/dataset_train.csv` exclusively)
**Search Strategy:** grid (1090 candidate setpoints evaluated)
**Random Seed:** 42
**Status:** `OPTIMAL`

---

## 1. Executive Summary

- **Optimization Status:** `OPTIMAL`
- **Domain Guard Outcome:** `VALID` (Optimal in-spec setpoints determined minimizing energy.)
- **Execution Time:** `159.30 ms`

- **Baseline Energy (Static SOP):** `2.449 kWh/cycle`
- **Optimized Energy (Adaptive Tuner):** `2.013 kWh/cycle`
- **Energy Savings:** `0.436 kWh/cycle` (`17.82%` reduction)
- **Simulator Quality Compliance:** Tensile `49.22 MPa` (Spec: 49.0–55.0 MPa) | Shrinkage `1.04%` (Spec: 0.80–1.60%)
- **All Hard Constraints Satisfied:** `True`

---

## 2. Actuator Recommendation vs. Baseline SOP

| Parameter | Units | Baseline SOP | Adaptive Recommendation | Machine Bounds |
| :--- | :--- | :--- | :--- | :--- |
| Melt Temperature ($T_{\text{melt}}$) | °C | 230.0 | 205.0 | [205.0, 255.0] |
| Injection Pressure ($P_{\text{inj}}$) | MPa | 100.0 | 141.0 | [65.0, 145.0] |
| Cooling Dwell Time ($t_{\text{cool}}$) | s | 20.0 | 12.0 | [12.0, 32.0] |

---

## 3. Surrogate Predictions vs. Authoritative Simulator Outcomes

| Performance Metric | Units | Surrogate Predicted | Realized Simulator | Baseline SOP | Prediction Error | In-Spec Spec |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Tensile Strength ($S$) | MPa | 49.79 | 49.22 | 51.99 | 0.565 | [49.0, 55.0] |
| Volumetric Shrinkage ($V_{\text{sh}}$) | % | 0.892 | 1.036 | 1.252 | 0.144 | [0.80, 1.60] |
| Specific Energy ($E$) | kWh/cycle | 2.013 | 2.013 | 2.449 | 0.000 | Minimize |

---

## 4. Engineering Limitations & Guardrail Discussion

1. **Surrogate Generalization Hull:** Random Forest exhibits high in-distribution fidelity ($R^2 > 0.90$) but flatlines outside training support. The Domain Guard actively intercepts OOD inputs (e.g. ambient temperatures > 32 °C or moistures > 0.50 wt%) to prevent unsupported surrogate predictions.
2. **Derivative-Free Grid Discretization:** The candidate search evaluates a finite bounded grid with local refinement. While ensuring zero gradient divergence on non-smooth tree surfaces, the theoretical global optimum lies in continuous space within the grid resolution.
3. **Decoupled Physical Validation:** All reported improvements are independently computed using the true simulator (`PolymerInjectionSimulator`) and matched noise seeds, ensuring causal integrity before claiming manufacturing benefits.
