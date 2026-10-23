
## 1. Project Overview & Official Problem Statement

In modern manufacturing, process parameters (such as melt temperature, injection pressure, and cooling dwell time) are frequently held at static nominal configurations validated solely under nominal laboratory conditions. However, in **Industry 5.0 circular manufacturing**, incoming raw materials—particularly post-consumer recycled (PCR) polymer resins—exhibit significant batch-to-batch variation in moisture content, melt flow index (MFI), and ambient intake conditions.

This project demonstrates how **adaptive parameter tuning** dynamically responds to shifting input material properties to eliminate quality drift, maintain structural tensile strength and volumetric shrinkage within tight specification tolerances, and minimize process energy consumption.

---

## 2. Core Operating Modes

The system provides two distinct, decoupled operational environments:

### Mode A: Research Simulation Environment
- Fully documented, phenomenologically grounded simulated polymer injection molding process.
- Non-linear physics coupling thermal degradation, logarithmic PVT pressure compaction, volatile moisture void creation, and exponential cooling stabilization.
- Matched-pair evaluation comparing fixed Standard Operating Procedure (SOP) control against adaptive ML surrogate tuning.
- 4 explicit Out-of-Distribution (OOD) generalization stress regimes.
- Quantitative evaluation directly against the independent true simulator.

### Mode B: Examiner Tabular Ingestion Engine
- Generic, schema-agnostic tabular ingestion engine accepting unseen CSV and Excel datasets.
- Automated column profiling (inferred numeric, categorical, datetime, identifier, and constant columns).
- Interactive schema mapping allowing users to assign target variables ($y$), input covariates ($X$), and genuine controllable actuators ($u$).
- Dynamic scikit-learn pipeline construction with leakage-free preprocessing and graceful handling of unseen categories.
- Strict scientific guardrails distinguishing predictive modeling from interventional/causal optimization.

---

## 3. Project Documentation Suite

All research decisions, derivations, and assessment items are documented in detail:

- **[Assessment Traceability Matrix](docs/assessment_traceability.md):** Complete bi-directional mapping between the official 100-mark rubric and project artifacts.
- **[Research Logbook](docs/research_logbook.md):** Chronological audit trail documenting hypotheses, code changes, actual test results, failures, and engineering pivots.
- **[Process Model Specification](docs/process_model.md):** Complete mathematical derivations, calibrated coefficients, unit conventions, and physical rationales.
- **[Dataset Documentation](docs/dataset_documentation.md):** In-distribution sampling distributions, split seeds, and formal OOD stress scenario formulations.

---

## 4. Repository Structure

```
AppliedAI/
├── config/
│   └── simulation_config.json      # Master simulator constants, bounds, noise parameters
├── data/
│   ├── synthetic/                  # Train, val, test, and OOD benchmark datasets
│   └── examiner_samples/           # Sample test datasets for Mode B demonstration
├── docs/
│   ├── assessment_traceability.md   # Rubric traceability matrix (100 marks)
│   ├── research_logbook.md         # Chronological experiment logbook
│   ├── process_model.md            # Physics equations and coefficient calibration
│   └── dataset_documentation.md    # Distribution specifications and OOD definitions
├── experiments/
│   ├── run_simulation_data.py          # Dataset generation script
│   ├── run_baseline_benchmarks.py      # Baseline benchmark runner
│   ├── run_surrogate_benchmarks.py     # Gate 1 surrogate benchmark runner
│   ├── run_closed_loop_evaluations.py  # Closed-loop evaluation runner
│   └── run_ablations.py                # Standalone offline surrogate feature ablation (sensor value analysis)
├── src/
│   ├── simulation/
│   │   ├── process_simulator.py        # Ground-truth manufacturing physics simulator
│   │   └── data_generator.py           # Reproducible ID & OOD data generation engine
│   ├── models/                         # Surrogate regression models & baselines (Phase 2-3)
│   ├── optimization/                   # Adaptive process parameter tuning & domain guard (Gate 2)
│   ├── profiling/                      # Dataset profiler & dynamic schema mapper (Phase 2)
│   ├── validation/                     # Gate 3-4 closed-loop evaluators & validation runners
│   │   ├── evaluator.py                # Gate 3 closed-loop evaluation engine
│   │   ├── run_gate3.py                # Gate 3 validation runner (CLI)
│   │   ├── gate4_evaluator.py          # Gate 4 robustness & ablation evaluator
│   │   └── run_gate4.py                # Gate 4 closed-loop robustness, sensitivity & ablation runner
│   └── web/                            # Lightweight Flask UI (Phase 5)
├── tests/                              # Comprehensive test suite (96 tests passing)
│   ├── test_simulation.py              # Simulator physics & data generation tests
│   ├── test_baselines.py               # Baseline models & static controller tests
│   ├── test_profiler.py                # Mode B profiler & schema validation tests
│   ├── test_surrogate_benchmark.py     # Surrogate benchmarking & leakage prevention tests
│   ├── test_adaptive_tuner.py          # Constrained optimizer unit tests
│   ├── test_gate2_tuning.py            # Gate 2 tuning & domain guard tests
│   ├── test_gate2_corrective_iteration.py # Gate 2 corrective iteration & adaptive margin tests
│   ├── test_gate3_validation.py        # Gate 3 closed-loop validation tests
│   └── test_gate4_evaluation.py        # Gate 4 robustness, sensitivity & ablation tests
├── requirements.txt                    # Pinned dependencies
└── README.md                           # Project documentation
```

---

## 5. Quickstart & Verification

### Running Automated Unit Tests
```bash
# Run full test suite (96 passing tests)
pytest tests/ -v

# Run individual test modules
pytest tests/test_simulation.py -v
pytest tests/test_gate4_evaluation.py -v
```

### Ablation & Validation Runners Distinction
This repository provides two distinct ablation/validation tools serving complementary engineering purposes:

1. **`experiments/run_ablations.py` (Offline Surrogate Feature Ablation):**
   - Evaluates machine learning surrogate accuracy degradation when individual input features (e.g., moisture, recycled content) are omitted from training.
   - Used to quantify sensor value and input feature sensitivity in offline model evaluation.

2. **`src/validation/run_gate4.py` (Gate 4 Closed-Loop System Validation):**
   - Evaluates 6 closed-loop controller variants (full corrected tuner vs. ablated margin/recycled variants vs. static SOP) directly against the authoritative physics simulator (`PolymerInjectionSimulator`).
   - Conducts systematic process noise robustness sweeps ($\sigma \in [0.0, 0.50]\text{ MPa}$), cross-seed stability checks, safety margin sweeps ($\Delta S \in [0.0, 2.20]\text{ MPa}$), and recycled content sensitivity sweeps.
   - Generates formal Gate 4 summary reports in `reports/gate4/`.

```bash
# Run formal Gate 4 closed-loop robustness and ablation validation
python -m src.validation.run_gate4

# Run standalone offline feature ablation experiment
python experiments/run_ablations.py
```

### Generating Synthetic Datasets
```bash
python experiments/run_simulation_data.py
```
