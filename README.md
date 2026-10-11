# AI-Based Adaptive Process Parameter Tuning

**Course:** 21CSE732P — Applied AI in Manufacturing, Industry 5.0  
**Project:** AI-Based Adaptive Process Parameter Tuning  
**Worklet:** No. 28  
**Tier:** Tier 3 — Advanced  
**Institution:** Applied AI Research Lab  

---

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
│   └── run_simulation_data.py      # Dataset generation script
├── src/
│   ├── simulation/
│   │   ├── process_simulator.py    # Ground-truth manufacturing physics simulator
│   │   └── data_generator.py       # Reproducible ID & OOD data generation engine
│   ├── models/                     # Surrogate regression models & baselines (Phase 2-3)
│   ├── optimization/               # Static SOP vs. Adaptive optimization controllers (Phase 3)
│   ├── profiling/                  # Dataset profiler & dynamic schema mapper (Phase 2)
│   └── web/                        # Lightweight Flask UI (Phase 5)
├── tests/
│   ├── test_simulation.py          # Unit tests for physical simulator and data generator
│   └── test_deliverables.py        # Compliance verification tests
├── requirements.txt                # Pinned dependencies
└── README.md                       # Project documentation
```

---

## 5. Quickstart & Verification

### Running Automated Unit Tests
```bash
pytest tests/test_simulation.py -v
```

### Generating Synthetic Datasets
```bash
python experiments/run_simulation_data.py
```
