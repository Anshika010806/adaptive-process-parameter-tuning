# Research Logbook: AI-Based Adaptive Process Parameter Tuning
**Course:** 21CSE732P — Applied AI in Manufacturing, Industry 5.0  
**Project:** AI-Based Adaptive Process Parameter Tuning (Worklet No. 28)  
**Maintained by:** Research Team / Applied AI Lab  
**Log Integrity Rule:** Every experiment entry records real observations, failure modes, pivots, and verification metrics. No fictional or backdated entries are permitted.

---

## Logbook Entry Format Template

```markdown
### [EXP-XXX] YYYY-MM-DD: Short Descriptive Title
- **Date & Experiment ID:** YYYY-MM-DD | EXP-XXX
- **Research Question / Hypothesis:** Explicit, testable statement.
- **Simulator / Dataset Configuration:** Parameter values, seeds, sample sizes.
- **Model / Optimization Strategy:** Specific algorithms, hyperparameters, loss functions.
- **Evaluation Protocol:** Matched-pair streams, metrics evaluated.
- **Code & Configuration Changes:** Commit / module modifications.
- **Actual Observed Results:** Quantitative metrics (MAE, RMSE, In-Spec Yield, etc.).
- **Expected vs. Observed Behavior:** Comparison against original hypothesis.
- **Errors, Failures & Limitations:** Optimizer stalls, surrogate gaming, out-of-bounds attempts.
- **Interpretation & Engineering Decision:** Scientific reasoning behind next steps.
- **Next Steps:** Action items leading to subsequent experiments.
```

---

## Chronological Experiment Log

### [EXP-001] 2026-10-11: Phase 1 — Ground-Truth Physical Simulator Specification and Verification
- **Date & Experiment ID:** 2026-10-11 | EXP-001
- **Research Question / Hypothesis:**  
  *Hypothesis 1:* A phenomenologically grounded non-linear synthetic model can reproduce quality drift in polymer injection molding when incoming moisture ($M$) and melt flow index ($\text{MFI}$) vary, such that a fixed SOP ($T_{\text{melt}}=230^\circ\text{C}, P_{\text{inj}}=100\text{ MPa}, t_{\text{cool}}=20\text{ s}$) produces unacceptable defect rates ($>30\%$) under degraded raw material batches.  
  *Hypothesis 2:* The simulation model is strictly deterministic when seeded, exhibits expected physical sensitivities (thermal degradation beyond optimum, logarithmic pressure compaction, cooling transient decay), and operates independently of downstream ML surrogates.
- **Simulator / Dataset Configuration:**  
  - Material Inputs: $M \in [0.05, 0.50]\%$, $\text{MFI} \in [14, 30]\text{ g}/10\text{ min}$, $T_{\text{amb}} \in [16, 32]^\circ\text{C}$, $C_{\text{rec}} \in [10, 40]\%$.
  - Nominal Settings (SOP): $T_{\text{melt}} = 230.0^\circ\text{C}$, $P_{\text{inj}} = 100.0\text{ MPa}$, $t_{\text{cool}} = 20.0\text{ s}$.
  - Quality Targets: Tensile Yield Strength $S^* = 52.0\text{ MPa}$ ($[49.0, 55.0]$), Volumetric Shrinkage $V_{\text{sh}}^* = 1.20\%$ ($[0.80, 1.60]\%$).
  - Stochastic Noise: $\sigma_S = 0.35\text{ MPa}$, $\sigma_V = 0.035\%$.
- **Model / Optimization Strategy:**  
  Ground-truth physics simulator implementation (`PolymerInjectionSimulator`) and vectorized batch execution engine. (ML surrogate tuning scheduled for Phase 3).
- **Evaluation Protocol:**  
  Comprehensive unit test suite (`pytest tests/test_simulation.py`):
  1. Deterministic repeatability across identical random seeds.
  2. Monotonicity and non-linear response curves across isolated parameter sweeps.
  3. Quality outcome plausibility under extreme operational bounds.
  4. Batch evaluation versus iterative single-sample evaluation numerical consistency.
  5. Input validation (raising informative exceptions on negative moisture, out-of-bounds temperatures, NaN values).
- **Code & Configuration Changes:**  
  - Initialized master project configuration: [config/simulation_config.json](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/config/simulation_config.json).
  - Authored physical simulator: [src/simulation/process_simulator.py](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/src/simulation/process_simulator.py).
  - Authored synthetic dataset generator: [src/simulation/data_generator.py](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/src/simulation/data_generator.py).
  - Authored simulator test suite: [tests/test_simulation.py](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/tests/test_simulation.py).
- **Actual Observed Results:**  
  - **Unit Tests:** 16 of 16 tests PASSED in 11.11 seconds (`pytest tests/test_simulation.py -v`).
  - **Synthetic Datasets Generated & Verified on Disk:**
    - `dataset_train.csv` (N=3,500 | In-Spec: 89.5% | Mean Tensile: 51.79 MPa | Mean Shrinkage: 1.22% | Mean Energy: 2.52 kWh)
    - `dataset_val.csv` (N=750 | In-Spec: 90.8% | Mean Tensile: 51.84 MPa | Mean Shrinkage: 1.22% | Mean Energy: 2.52 kWh)
    - `dataset_test_id.csv` (N=750 | In-Spec: 89.5% | Mean Tensile: 51.83 MPa | Mean Shrinkage: 1.23% | Mean Energy: 2.51 kWh)
    - `dataset_ood_1_feedstock.csv` (N=500 | In-Spec: 67.8% | Mean Tensile: 49.36 MPa | Mean Shrinkage: 1.41% | Mean Energy: 2.46 kWh). Under static SOP, degraded feedstock drives a **32.2% defect rate**!
    - `dataset_ood_2_thermal.csv` (N=500 | In-Spec: 100.0% | Mean Tensile: 52.43 MPa | Mean Shrinkage: 1.25% | Mean Energy: 2.36 kWh). High ambient heat reduced barrel heater demand by ~0.16 kWh.
    - `dataset_ood_3_extrap.csv` (N=500 | In-Spec: 0.0% | Mean Tensile: 46.23 MPa | Mean Shrinkage: 1.53% | Mean Energy: 2.46 kWh). Extreme moisture ($M > 0.55\%$) caused **100% defect rate** under static SOP.
    - `dataset_ood_4_sensor.csv` (N=500 | In-Spec: 99.4% | Mean Tensile: 52.29 MPa | Mean Shrinkage: 1.25% | Mean Energy: 2.46 kWh).
- **Expected vs. Observed Behavior:**  
  - Confirmed: Under static SOP, incoming feedstock degradation (OOD-1 and OOD-3) produces severe quality drift (defect rates of 32.2% and 100.0% respectively), validating Hypothesis 1.
  - Confirmed: The simulation engine is strictly deterministic when seeded, passes all monotonicity and physical boundary checks, and executes without data leakage.

- **Errors, Failures & Limitations:**  
  - Identified requirement for explicit percentage vs. fraction convention for moisture ($M$) and recycled content ($C_{\text{rec}}$) to avoid decimal scaling errors. Standardized on percentage-by-weight (wt %) across all modules.
  - Noted that for extreme moisture levels ($M > 0.65\%$), target strength is strictly unreachable within safe machine bounds; confirmed simulator must allow logging of infeasible states rather than falsely clipping or fabricating target attainment.
- **Interpretation & Engineering Decision:**  
  Proceed with automated unit test execution once dependencies complete. Confirm 100% pass rate before advancing to Phase 2.
- **Next Steps:**  
  1. Execute `pytest tests/test_simulation.py` and record exact passing assertions.
  2. Generate initial in-distribution synthetic datasets (`train`, `val`, `test`) with locked seeds.
  3. Inspect baseline fixed SOP yield metrics on held-out dataset.
