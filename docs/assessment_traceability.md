# Assessment Traceability & Reconciliation Matrix
**Course:** 21CSE732P — Applied AI in Manufacturing, Industry 5.0
**Cohort & Slot:** Sem-5, Batch-1, Slot-B | AY 2026-27 (Odd)
**Faculty Guide:** Dr. Udendharn
**Project:** AI-Based Adaptive Process Parameter Tuning (Worklet No. 28, Tier 3)
**Reference Document:** `Mark Split 21CSE732P rubrics .pdf` (Reconciled & Rechecked)
**Checkpoint Phase:** PBL-II / Gate 4 Validation Checkpoint

---

## 1. Rubric Integrity & Assessment Policy

> **Universal Anti-Shortcut Policy:**
> In strict compliance with the course rubric, **no marks are claimed as earned or awarded by this project**. Marks are strictly awarded by the faculty guide during official oral reviews and evaluation checkpoints.
>
> This matrix tracks internal technical status across four distinct engineering dimensions:
> 1. **Implementation Status:** The presence of concrete, executable code on disk.
> 2. **Verification & Test Status:** Automated tests in `pytest` verifying correctness, bounds, and lack of leakage.
> 3. **Documentation Evidence:** Traceable markdown documentation citing physical equations, seeds, and logs.
> 4. **Official Assessment Status:** Pending formal presentation at the scheduled academic review window.

---

## 2. Reconciled Traceability Matrix (100 Marks Total)

The table below reconciles every checkpoint, sub-criterion, and mark allocation against `Mark Split 21CSE732P rubrics .pdf`:

| Checkpoint & Timeline | Sub-Criterion from Official Rubric | Allocated Marks | Technical Implementation Artifact | Test & Verification Evidence | Engineering Status | External Faculty Assessment Status |
| :--- | :--- | :---: | :--- | :--- | :---: | :---: |
| **FP-I**<br>(Weeks 1–3) | **1. Problem Statement, USP & R&D Component:**<br>Understanding of assigned worklet's problem framing and manufacturing domain. | 4 | [docs/process_model.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/process_model.md)<br>[src/simulation/process_simulator.py](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/src/simulation/process_simulator.py) | Nonlinear physics equations; drift demonstrated under static SOP. | **Implemented & Documented** | Awaiting FP-I Formal Review |
| **FP-I**<br>(Weeks 1–3) | **2. Literature & Public-Dataset Survey:**<br>Survey of adaptive manufacturing tuning & benchmark datasets relevant to worklet. | 3 | [docs/literature_survey.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/literature_survey.md) | Verified peer-reviewed citations (Chen & Gao, Zhao et al., Khosravani, Hopmann) & UCI AI4I / NIST datasets. | **Implemented & Documented** | Awaiting FP-I Formal Review |
| **FP-I**<br>(Weeks 1–3) | **3. Proposed Approach & Team Work-Plan:**<br>Clarity of proposed methodology and 20-day phased development schedule. | 3 | [docs/assessment_traceability.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/assessment_traceability.md)<br>`README.md` | Phased sprint schedule mapped to deliverables and deliverables tracker. | **Implemented & Documented** | Awaiting FP-I Formal Review |
| **FP-II**<br>(Weeks 4–6) | **1. Dataset Acquisition / Construction Plan:**<br>Plan for how dataset is curated, augmented, or synthesized with statistical distributions. | 4 | [docs/dataset_documentation.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/dataset_documentation.md)<br>[src/simulation/data_generator.py](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/src/simulation/data_generator.py) | Explicit truncated normal/beta distributions, locked seeds, 4 OOD stress definitions. | **Implemented & Documented** | Awaiting FP-II Formal Review |
| **FP-II**<br>(Weeks 4–6) | **2. Tooling / Tech-Stack Setup:**<br>Tooling and stack matching catalog specification (Python, scikit-learn, pytest). | 3 | `requirements.txt`<br>`.venv/`<br>[tests/test_simulation.py](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/tests/test_simulation.py) | Automated test suite verified passing (16/16 simulator tests). | **Implemented & Tested** | Awaiting FP-II Formal Review |
| **FP-II**<br>(Weeks 4–6) | **3. Research Logbook — First Entries:**<br>Initial entries present documenting setup decisions, hypotheses, and initial failures. | 3 | [docs/research_logbook.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/research_logbook.md) | Entry `[EXP-001]` documenting setup, hypotheses, and unit test pass. | **Implemented & Documented** | Awaiting FP-II Formal Review |
| **PBL-I**<br>(Weeks 7–9) | **1. Dataset Finalised & Documented:**<br>Documented construction methodology, leakage prevention, and data files on disk. | 5 | [data/synthetic/](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/data/synthetic/)<br>[docs/dataset_documentation.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/dataset_documentation.md) | 7 synthetic datasets generated ($N=5,000$ ID + 4 OOD stress sets) without leakage. | **Implemented & Documented** | Awaiting PBL-I Milestone Review |
| **PBL-I**<br>(Weeks 7–9) | **2. Working Baseline Model & Initial Results:**<br>Working baseline models and first documented results across targets. | 5 | [src/models/baseline.py](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/src/models/baseline.py)<br>[src/optimization/static_controller.py](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/src/optimization/static_controller.py)<br>`experiments/run_baseline_benchmarks.py` | Multi-output Dummy ($R^2=-0.001$), Linear ($R^2=0.759 / 0.946$), Ridge ($R^2=0.759 / 0.946$), Static SOP (100% ID, 67.8% OOD-1). | **Implemented & Tested** | Awaiting PBL-I Milestone Review |
| **PBL-I**<br>(Weeks 7–9) | **3. Research Logbook Depth (Iteration & Pivots):**<br>Documented iterations, bugs caught by tests, and pivot rationales. | 5 | [docs/research_logbook.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/research_logbook.md) | Entry `[EXP-002]` documenting float ID detection bug fix, non-linear $R^2$ gap, and Mode B schema tests. | **Implemented & Documented** | Awaiting PBL-I Milestone Review |
| **PBL-II**<br>(Weeks 10–12) | **1. Comparative Benchmark ($\ge 2$ Methods):**<br>Benchmarking $\ge 2$ models/methods with quantitative results. | 7 | [src/models/surrogate_benchmark.py](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/src/models/surrogate_benchmark.py)<br>`experiments/run_surrogate_benchmarks.py` | Benchmarked Ridge vs DecisionTree vs RandomForest on identical splits (`tests/test_surrogate_benchmark.py`, 6 passing tests). | **Implemented & Tested** | Awaiting PBL-II Review |
| **PBL-II**<br>(Weeks 10–12) | **2. Ablation or Robustness Test with Results:**<br>Ablation study (sensing value) and noise robustness tests. | 7 | Planned: `experiments/run_ablations.py`<br>`experiments/run_ood_evaluations.py` | Feature ablation (moisture sensor), sensor noise injection, weight trade-offs. | **Planned (Phase 4)** | Awaiting PBL-II Review |
| **PBL-II**<br>(Weeks 10–12) | **3. Research Logbook (Failures/Pivots & Progress):**<br>Logbook documentation of optimizer failure modes and progress vs plan. | 6 | [docs/research_logbook.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/research_logbook.md) | Planned entries `[EXP-003]` and `[EXP-004]`. | **Planned (Phase 4)** | Awaiting PBL-II Review |
| **PBL-III**<br>(Weeks 13–15) | **1. Final Quantitative Results:**<br>Final quantitative metrics (In-Spec Yield, Cpk, MAE/RMSE, Energy). | 8 | Planned: `experiments/run_final_benchmarks.py` | Closed-loop adaptive vs fixed SOP yield curves and energy tradeoffs. | **Planned (Phase 4)** | Awaiting PBL-III Review |
| **PBL-III**<br>(Weeks 13–15) | **2. Demo Run Live on Unseen / Held-Out Data:**<br>Live demonstration readiness on unknown examiner dataset. | 7 | [src/profiling/](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/src/profiling/) (Engine Built)<br>Planned: `src/web/` (Interactive UI) | Mode B ingestion engine tested on 3 diverse sample datasets; UI integration pending. | **Partially Implemented (Phase 2/5)** | Awaiting PBL-III Review |
| **PBL-III**<br>(Weeks 13–15) | **3. Completeness vs. Worklet Deliverables:**<br>Compliance with all 4 mandatory worklet core deliverables. | 5 | All modules & test suites | Simulator, adaptive controller, OOD study, and research logbook. | **Planned (Phase 5)** | Awaiting PBL-III Review |
| **R21 Report & Viva**<br>(End of Semester) | **1. Final Report Structure & Technical Accuracy:**<br>Comprehensive technical report covering physics, modeling, and results. | 10 | Planned: `docs/final_report.md` | Formal IEEE-style technical report. | **Planned (Phase 6)** | Awaiting Final Viva |
| **R21 Report & Viva**<br>(End of Semester) | **2. Live Viva — Justification of Decisions:**<br>Ability to defend physical equations, assumptions, and surrogate choices live. | 10 | Planned: `docs/viva_defense.md` | Viva preparation guide addressing physical limits and causal guardrails. | **Planned (Phase 6)** | Awaiting Final Viva |
| **R21 Report & Viva**<br>(End of Semester) | **3. Research Logbook — Semester-Long Trail:**<br>Audit trail of experiments, failures, and decisions throughout the term. | 5 | [docs/research_logbook.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/research_logbook.md) | Continuous chronological log entries from EXP-001 through final demo. | **Active & Maintained** | Awaiting Final Viva |
| **Total Marks** | | **100** | | | | |

---

## 3. Four Core Worklet Deliverables Audit

| Mandatory Worklet Deliverable | Implementation Module | Documentation File | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **1. Documented Simulated Process Model** linking input variability to quality outcomes | [src/simulation/process_simulator.py](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/src/simulation/process_simulator.py) | [docs/process_model.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/process_model.md) | `tests/test_simulation.py` (16 passing tests) |
| **2. Adaptive Tuning Model** trained and tested against simulation | Planned: `src/optimization/adaptive_tuner.py` | [docs/process_model.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/process_model.md) (Formulation ready) | Baseline models verified in `tests/test_baselines.py` |
| **3. Generalization Study** on input distributions not used during training | `src/simulation/data_generator.py` (4 OOD sets generated) | [docs/dataset_documentation.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/dataset_documentation.md) | 4 OOD CSV files on disk; benchmark script planned |
| **4. Research Logbook** documenting experiments, decisions, failures, and progress | [docs/research_logbook.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/research_logbook.md) | [docs/research_logbook.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/research_logbook.md) | Entries EXP-001 and EXP-002 completed |

---

## 4. Phase Verification Checkpoint Log

-**Phase 1 Milestone (Weeks 1–3 Scope / FP-I, FP-II):**
  - Physical simulator implemented, configured, and tested (`pytest tests/test_simulation.py` — 16 passed).
  - 7 synthetic datasets generated without data leakage.
  - Initial logbook entry `[EXP-001]` recorded.
-**Phase 2 Milestone (Weeks 4–9 Scope / FP-II, PBL-I):**
  - Baseline multi-output models (Dummy, Linear, Ridge) and Static SOP controller implemented.
  - Mode B Dataset Profiler, Schema Validator, and Dynamic Pipeline Builder implemented.
  - 3 diverse examiner sample datasets created and whitelisted in `.gitignore`.
  - Comprehensive test suite passed (`pytest tests/` — 28 passed).
  - Logbook entry `[EXP-002]` recorded with unrounded baseline metrics and physical analysis.
-**Phase 2 Documentation Checkpoint:**
  - Official marks split reconciled against `Mark Split 21CSE732P rubrics .pdf` (Faculty: Dr. Udendharn).
  - Authored [docs/literature_survey.md](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/docs/literature_survey.md) addressing FP-I.2 with genuine peer-reviewed citations and public dataset references.
-**Phase 3 Gate 1 Milestone (PBL-II.1 Completed):**
  - Comparative surrogate benchmarking implemented: [src/models/surrogate_benchmark.py](file:///c:/Users/SHANTI%20MISHRA/AppliedAI/src/models/surrogate_benchmark.py).
  - Evaluated Ridge, DecisionTree, and RandomForest across held-out In-Distribution test set and all 4 OOD stress datasets.
  - Hyperparameters tuned on validation fold without target leakage.
  - Test suite expanded to 34 passing tests (`pytest tests/` — 34 passed).
  - Technical readiness confirmed: **39 / 100 marks** fully supported by verified code, models, and documentation on disk, awaiting official faculty assessment.
-**Phase 3 Gate 2 Milestone (PBL-II.2 Completed):**
  - Implemented Domain Guard ([src/optimization/domain_guard.py](file:///c:/AppliedAI/adaptive-process-parameter-tuning/src/optimization/domain_guard.py)) for physical bounds validation, extreme uncompensable condition detection, and strict out-of-training-support rejection (`OOD_REJECTED`).
  - Implemented surrogate loading and training interface ([src/optimization/surrogate_loader.py](file:///c:/AppliedAI/adaptive-process-parameter-tuning/src/optimization/surrogate_loader.py)) utilizing `dataset_train.csv` exclusively.
  - Implemented constrained derivative-free adaptive tuning engine in [src/optimization/adaptive_tuner.py](file:///c:/AppliedAI/adaptive-process-parameter-tuning/src/optimization/adaptive_tuner.py) minimizing energy subject to hard quality constraints (Tensile 49–55 MPa, Shrinkage 0.80–1.60%, machine actuator bounds).
  - Implemented authoritative simulator validation with matched noise realization in [src/optimization/simulator_validator.py](file:///c:/AppliedAI/adaptive-process-parameter-tuning/src/optimization/simulator_validator.py).
  - Implemented Gate 2 execution entry point: [src/optimization/run_gate2.py](file:///c:/AppliedAI/adaptive-process-parameter-tuning/src/optimization/run_gate2.py).
  - Saved verified Gate 2 report artifacts in `reports/gate2/` (`.json`, `.csv`, `.md`).
  - Verified default smoke-test run: Baseline energy 2.449 kWh -> Tuned energy 2.013 kWh (17.82% reduction), Tensile 49.22 MPa (in spec), Shrinkage 1.036% (in spec), 159.3 ms execution latency.
  - Full automated test suite expanded to **55 tests — 100% PASS** (`pytest tests/`).