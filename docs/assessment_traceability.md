# Assessment Traceability Matrix
**Course:** 21CSE732P — Applied AI in Manufacturing, Industry 5.0  
**Project:** AI-Based Adaptive Process Parameter Tuning  
**Worklet:** No. 28 (Tier 3 — Advanced)  
**Implementation Window:** 20 Days  
**Total Target Marks:** 100 Marks  
**Last Updated:** Phase 1 Initialization  

---

## 1. Traceability Overview

This document provides a rigorous, bi-directional traceability mapping between the official 100-mark assessment rubric for Worklet No. 28 and the tangible code, data, experiments, documentation, and validation artifacts in this repository.

> **Integrity Policy:** No criterion is marked as completed until verifiable supporting evidence exists on disk and has passed automated testing.

---

## 2. Assessment Traceability Matrix

| Rubric Component | Marks | Specific Rubric Requirement | Implementation Module / Evidence File | Verification & Test Evidence | Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **FP-I.1** | 4 | Understanding of the worklet problem statement, USP, and R&D component | [docs/process_model.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/process_model.md)<br>[docs/research_logbook.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/research_logbook.md) | Documented non-linear physics, drift under static parameters, and closed-loop compensation USP. | **Completed (Phase 1)** |
| **FP-I.2** | 3 | Literature and public-dataset survey relevant to the worklet | [docs/literature_survey.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/literature_survey.md) | Survey of adaptive tuning in Industry 5.0 circular plastics manufacturing and benchmark datasets. | **Planned (Days 2–3)** |
| **FP-I.3** | 3 | Proposed approach and team work-plan | [docs/assessment_traceability.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/assessment_traceability.md)<br>`README.md` | Complete 20-day phased development schedule mapped to official worklet deliverables. | **Completed (Phase 1)** |
| **FP-II.1** | 4 | Dataset acquisition, construction, or augmentation plan | [docs/dataset_documentation.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/dataset_documentation.md)<br>[src/simulation/data_generator.py](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/src/simulation/data_generator.py) | Explicit statistical distributions, random seeds, and 4 OOD stress scenario formulations. | **Completed (Phase 1)** |
| **FP-II.2** | 3 | Technology-stack setup matching the worklet | `requirements.txt`<br>`tests/test_simulation.py` | Python 3.12, NumPy, Pandas, pytest verified with 16/16 tests passing. | **Completed (Phase 1)** |
| **FP-II.3** | 3 | Initial research logbook entries, including failed attempts | [docs/research_logbook.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/research_logbook.md) | Entry EXP-001 (Setup, design decisions, hypothesis formulation, unit test log). | **Completed (Phase 1)** |
| **PBL-I.1** | 5 | Finalized, documented dataset and construction methodology | [data/synthetic/](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/data/synthetic/)<br>[docs/dataset_documentation.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/dataset_documentation.md) | Generated $N=5000$ train/val/test splits + 4 OOD datasets on disk with zero data leakage. | **Completed (Phase 1)** |
| **PBL-I.2** | 5 | Working baseline model and initial results | `src/models/baseline.py`<br>`src/optimization/static_controller.py` | Fixed SOP baseline yield vs DummyRegressor and LinearRegressor performance metrics. | Planned (Days 4–6) |
| **PBL-I.3** | 5 | Research logbook documenting iterations and pivots | [docs/research_logbook.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/research_logbook.md) | Entry EXP-002: Baseline defect rate verification and initial surrogate convergence. | Planned (Days 4–6) |
| **PBL-II.1** | 7 | Comparative benchmarking of at least two methods | `src/models/surrogate_benchmark.py`<br>`experiments/run_surrogate_benchmarks.py` | Comparative table of MAE, RMSE, and $R^2$ across Ridge, Decision Tree, and Random Forest. | Planned (Days 7–10) |
| **PBL-II.2** | 7 | Ablation or robustness experiments with results | `experiments/run_ablations.py`<br>`experiments/run_ood_evaluations.py` | Feature ablation (moisture sensor ablation), noise injection ($\sigma \in [2\%, 20\%]$), weight trade-offs. | Planned (Days 11–14) |
| **PBL-II.3** | 6 | Documented failures, pivots, and progress in research logbook | [docs/research_logbook.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/research_logbook.md) | Entries EXP-003 & EXP-004: Surrogate gaming failures, optimizer stall on step functions. | Planned (Days 11–14) |
| **PBL-III.1** | 8 | Final quantitative results | `experiments/run_final_benchmarks.py`<br>`docs/final_report.md` | In-spec yield comparison (Static vs Adaptive), Cpk improvements, energy tradeoffs. | Planned (Days 11–14) |
| **PBL-III.2** | 7 | Live demonstration on previously unseen or held-out data | `src/web/app.py`<br>`src/profiling/dataset_profiler.py` | Examiner Mode (Mode B): dynamic CSV/XLSX profiling, dynamic schema mapping, fallback. | Planned (Days 15–17) |
| **PBL-III.3** | 5 | Completion of the official worklet deliverables | All modules & tests | Independent simulator, surrogate tuner, OOD generalization study, and research logbook. | Planned (Days 15–17) |
| **Viva/Report.1** | 10 | Technical accuracy, completeness, and report structure | `docs/final_report.md` | Formal IEEE/academic structured report covering problem, theory, equations, and metrics. | Planned (Days 18–20) |
| **Viva/Report.2** | 10 | Ability to justify modeling and engineering decisions during viva | `docs/viva_defense.md` | Viva defense guide answering physical assumptions, surrogate selection, and causal limitations. | Planned (Days 18–20) |
| **Viva/Report.3** | 5 | Semester-long research logbook | [docs/research_logbook.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/research_logbook.md) | Complete chronological audit trail with hypotheses, actual results, failures, and pivots. | Continuous |

---

## 3. Four Core Worklet Deliverables Traceability

The official Worklet No. 28 specification mandates four primary deliverables:

1. **Documented Simulated Process Model linking input variability to quality outcomes:**
   - Implemented in: [src/simulation/process_simulator.py](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/src/simulation/process_simulator.py)
   - Mathematically documented in: [docs/process_model.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/process_model.md)
   - Verified by: `tests/test_simulation.py` (16 passed)

2. **Adaptive Tuning Model trained and tested against this simulation:**
   - Implemented in: `src/models/surrogate_pipeline.py` & `src/optimization/adaptive_tuner.py`
   - Verified by: Matched-pair evaluation against independent simulator in `tests/test_optimization.py`

3. **Generalization Study on input-variability distributions not used during training:**
   - Implemented in: `experiments/run_ood_evaluations.py`
   - Documented in: [docs/dataset_documentation.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/dataset_documentation.md) (4 distinct OOD regimes generated in `data/synthetic/`)

4. **Research Logbook documenting experiments, decisions, failures, and progress:**
   - Maintained in: [docs/research_logbook.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/research_logbook.md)

---

## 4. Milestone Verification Log

*This section is updated as each milestone is executed and automated tests pass.*

- **Phase 1 (Milestone 1 - Completed):**
  - Physical simulator implementation, configuration parameters, and unit tests.
  - Automated Test Evidence: `pytest tests/test_simulation.py -v` (16 passed in 11.11s).
  - Data Artifacts Generated:
    - `dataset_train.csv` (N=3500, 681.2 KB)
    - `dataset_val.csv` (N=750, 145.6 KB)
    - `dataset_test_id.csv` (N=750, 145.6 KB)
    - `dataset_ood_1_feedstock.csv` (N=500, 78.0 KB)
    - `dataset_ood_2_thermal.csv` (N=500, 77.6 KB)
    - `dataset_ood_3_extrap.csv` (N=500, 78.2 KB)
    - `dataset_ood_4_sensor.csv` (N=500, 78.3 KB)
  - Documentation Artifacts: [docs/process_model.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/process_model.md), [docs/dataset_documentation.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/dataset_documentation.md), [docs/research_logbook.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/research_logbook.md), [config/simulation_config.json](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/config/simulation_config.json).

