# Dataset Documentation & Methodology
**Course:** 21CSE732P — Applied AI in Manufacturing, Industry 5.0  
**Project:** AI-Based Adaptive Process Parameter Tuning (Worklet No. 28)  
**Document:** Dataset Schema, Statistical Distributions, Seeds, and OOD Regimes  
**Version:** 1.0.0 (Phase 1 Approved)  

---

## 1. Data Generation Philosophy & Leakage Prevention

The data pipeline for Worklet No. 28 generates synthetic tabular datasets from the true non-linear polymer injection simulator (`PolymerInjectionSimulator`). 

### Core Scientific Principles:
1. **Strict Decoupling:** The datasets contain strictly observational tuples $(x_{\text{mat}}, u, y)$ mimicking shop-floor cavity sensor logs. Downstream ML models never receive direct access to the simulator's analytical equations.
2. **Reproducibility:** All sampling processes are seeded deterministically with explicit seed declarations.
3. **Strict Leakage Prevention:**
   - Splitting occurs **before** any feature normalization or pipeline fitting.
   - Any transformer (e.g., `StandardScaler`, `OneHotEncoder`) is fit **solely** on the training fold and applied to validation/test sets without target visibility.
4. **Matched-Pair Evaluation Protocol:** When evaluating the Static SOP baseline versus the Adaptive Controller, the identical material perturbation sequence is fed to both systems.

---

## 2. In-Distribution (ID) Dataset Specifications

In-distribution data simulates normal shop-floor operating conditions with standard batch-to-batch variability:

### 2.1 Material Disturbance Distributions ($x_{\text{mat}}$)
- **Moisture Content ($M$, wt %):** Truncated Gaussian distribution:
  $$M \sim \mathcal{N}(\mu = 0.15, \sigma = 0.06), \quad \text{clipped to } [0.05, 0.45]\%$$
- **Melt Flow Index ($\text{MFI}$, g/10 min):** Gaussian distribution:
  $$\text{MFI} \sim \mathcal{N}(\mu = 22.0, \sigma = 3.0), \quad \text{clipped to } [14.0, 30.0]\text{ g}/10\text{ min}$$
- **Ambient Intake Temperature ($T_{\text{amb}}$, °C):** Gaussian distribution:
  $$T_{\text{amb}} \sim \mathcal{N}(\mu = 24.0, \sigma = 2.5), \quad \text{clipped to } [18.0, 30.0]^\circ\text{C}$$
- **Recycled Content Ratio ($C_{\text{rec}}$, wt %):** Beta distribution:
  $$C_{\text{rec}} \sim 10.0 + 30.0 \times \text{Beta}(\alpha = 2.5, \beta = 2.5), \quad \text{spanning } [10.0, 40.0]\%$$

### 2.2 Exploration Control Parameters ($u$) during Training Data Generation
To allow surrogate models to learn the response surface across the feasible operational space, controllable machine settings are sampled via Latin Hypercube Sampling (LHS) / Uniform space-filling sampling:
- **Melt Temperature ($T_{\text{melt}}$):** $\mathcal{U}(205.0, 255.0)^\circ\text{C}$
- **Injection Pressure ($P_{\text{inj}}$):** $\mathcal{U}(65.0, 145.0)\text{ MPa}$
- **Cooling Time ($t_{\text{cool}}$):** $\mathcal{U}(12.0, 32.0)\text{ s}$

### 2.3 Split Sizes and Seed Assignments

| Dataset Partition | Sample Count ($N$) | Proportion | Random Seed | Primary Purpose |
| :--- | :---: | :---: | :---: | :--- |
| **Training Set** | $3,500$ | $70\%$ | `SEED = 42` | Surrogate model fitting and pipeline learning. |
| **Validation Set** | $750$ | $15\%$ | `SEED = 101` | Model selection and hyperparameter optimization. |
| **In-Distribution Test Set** | $750$ | $15\%$ | `SEED = 202` | Unbiased evaluation under nominal distribution. |
| **Total In-Distribution** | **5,000** | **100%** | — | — |

---

## 3. Mandatory Out-of-Distribution (OOD) Stress Scenarios

To satisfy the official worklet requirement of a generalization study on input-variability distributions not used during training, 4 distinct stress regimes are formulated:

### Scenario OOD-1: Feedstock Quality Shift (Degraded Recycled Lot)
- **Physical Context:** A batch of low-grade, improperly dried recycled polymer arrives from a secondary vendor.
- **Distribution Shift:**
  - $M \sim \mathcal{N}(\mu = 0.42, \sigma = 0.05)$, clipped to $[0.30, 0.55]\%$ (mean moisture increased by $+180\%$).
  - $\text{MFI} \sim \mathcal{N}(\mu = 16.0, \sigma = 2.0)$, clipped to $[11.0, 20.0]$ (significantly higher molecular weight / viscosity).
- **Test Set Size:** $N = 500$ samples, `SEED = 301`.
- **Target Question:** Can the adaptive controller increase injection pressure and adjust temperature to prevent tensile failure without excessive flash?

### Scenario OOD-2: Environmental Thermal Shift (Extreme Factory Heatwave)
- **Physical Context:** Extreme summer ambient conditions on the factory floor without climate control.
- **Distribution Shift:**
  - $T_{\text{amb}} \sim \mathcal{N}(\mu = 36.5, \sigma = 2.0)$, clipped to $[33.0, 42.0]^\circ\text{C}$ (mean ambient temp shifted $+12.5^\circ\text{C}$).
- **Test Set Size:** $N = 500$ samples, `SEED = 302`.
- **Target Question:** Does the optimizer exploit reduced barrel heating energy or adjust cooling dwell to prevent warpage?

### Scenario OOD-3: Extrapolation Beyond Training Support
- **Physical Context:** Raw material condition strictly outside the convex hull seen during training.
- **Distribution Shift:**
  - $M \in [0.55, 0.70]\%$ (strictly $> 0.50\%$ training upper bound).
- **Test Set Size:** $N = 500$ samples, `SEED = 303`.
- **Target Question:** Does the ML surrogate make wildly inaccurate predictions (surrogate gaming), and how does the optimizer behave when the quality target is physically unreachable?

### Scenario OOD-4: Sensor Measurement Noise & Corrupted Disturbances
- **Physical Context:** Shop-floor material moisture sensor lens fouled, injecting high observation variance.
- **Distribution Shift:**
  - Nominal distributions, but measured $x_{\text{mat}}$ inputs are corrupted with $15\%$ additive zero-mean Gaussian measurement noise.
- **Test Set Size:** $N = 500$ samples, `SEED = 304`.
- **Target Question:** How robust is the adaptive parameter recommendation when sensor telemetry is noisy?

---

## 4. Tabular Data Schema

Every generated dataset is persisted to CSV with the following standardized header columns:

```csv
cycle_id,moisture_pct,melt_flow_index,ambient_temp_c,recycled_pct,melt_temp_c,injection_pressure_mpa,cooling_time_s,tensile_strength_mpa,volumetric_shrinkage_pct,energy_kwh,in_spec_flag
```

Where:
- `cycle_id`: Unique integer sequential identifier.
- `moisture_pct`: Feedstock moisture content ($M$, wt %).
- `melt_flow_index`: Melt Flow Index ($\text{MFI}$, g/10 min).
- `ambient_temp_c`: Ambient factory temperature ($T_{\text{amb}}$, °C).
- `recycled_pct`: Recycled material blend ratio ($C_{\text{rec}}$, wt %).
- `melt_temp_c`: Barrel melt temperature setpoint ($T_{\text{melt}}$, °C).
- `injection_pressure_mpa`: Injection hold pressure ($P_{\text{inj}}$, MPa).
- `cooling_time_s`: Mold cooling dwell time ($t_{\text{cool}}$, s).
- `tensile_strength_mpa`: Realized part tensile yield strength ($S$, MPa).
- `volumetric_shrinkage_pct`: Realized volumetric shrinkage ($V_{\text{sh}}$, %).
- `energy_kwh`: Realized specific process energy ($E_{\text{proc}}$, kWh).
- `in_spec_flag`: Boolean integer ($1$ if $S \in [49.0, 55.0]$ and $V_{\text{sh}} \in [0.80, 1.60]$; $0$ otherwise).
