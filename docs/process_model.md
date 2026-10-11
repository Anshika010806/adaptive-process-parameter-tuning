# Process Model Specification: Polymer Injection Molding under Feedstock Variability
**Course:** 21CSE732P — Applied AI in Manufacturing, Industry 5.0  
**Project:** AI-Based Adaptive Process Parameter Tuning (Worklet No. 28)  
**Document:** Mathematical Process Model Specification & Calibration Rationale  
**Version:** 1.0.0 (Phase 1 Approved)  

---

## 1. Executive Summary & Scientific Disclaimer

This document defines the mathematical formulation, physical phenomenological basis, variable definitions, and coefficient calibrations for the simulated manufacturing process in Worklet No. 28.

> **Scientific Disclaimer:**  
> This model is an **illustrative, phenomenologically grounded synthetic research testbed** designed specifically for evaluating adaptive parameter tuning algorithms under input material variability. While its equations are informed by established polymer rheology (Arrhenius viscosity behavior, pressure compaction, thermal degradation, and cooling crystallization dynamics), it is **not** an experimentally validated commercial finite-element solver (such as Autodesk Moldflow). It is intentionally constructed to provide a reproducible, computationally lightweight, non-linear environment with stochastic noise to benchmark predictive surrogates and optimization controllers.

---

## 2. Industrial Manufacturing Scenario

In **Industry 5.0**, sustainable manufacturing demands the integration of post-consumer recycled (PCR) polymer resins into injection molding production lines. However, recycled feedstocks suffer from severe batch-to-batch variation in:
1. **Moisture Content ($M$):** Absorbed humidity during storage and reprocessing.
2. **Melt Flow Index ($\text{MFI}$):** Molecular weight variance caused by repeated thermal processing.
3. **Ambient Intake Temperature ($T_{\text{amb}}$):** Seasonal and diurnal factory shop-floor thermal shifts.
4. **Recycled Ratio ($C_{\text{rec}}$):** Variable blend ratios between virgin and regrind material.

Under standard industrial operations (Standard Operating Procedure / SOP), machine settings—such as barrel melt temperature, injection pressure, and cooling time—are maintained at **fixed nominal values**. When a high-moisture or low-MFI batch arrives, fixed parameters lead to significant **quality drift**, including severe tensile strength loss (due to moisture-induced steam micro-voids and hydrolytic degradation) or volumetric shrinkage violations (due to viscosity-driven mold under-packing). 

The goal of the adaptive system is to continuously adjust machine actuators to preserve part quality within strict engineering tolerance limits while minimizing process energy.

---

## 3. Mathematical Notation & Engineering Units Convention

### Percentage vs. Fraction Convention
To prevent dimensional errors and ambiguity across ML datasets and physical equations, the following convention is strictly enforced:
- **Moisture Content ($M$):** Expressed as **Percentage by Weight (wt %)**, $M \in [0.05, 0.50]$. A value of $0.15$ denotes $0.15\%$.
- **Recycled Content ($C_{\text{rec}}$):** Expressed as **Percentage by Weight (wt %)**, $C_{\text{rec}} \in [10.0, 40.0]$. A value of $25.0$ denotes $25.0\%$.
- **Volumetric Shrinkage ($V_{\text{sh}}$):** Expressed as **Percentage (%)**, $V_{\text{sh}} \in [0.80, 1.60]\%$. A value of $1.20$ denotes $1.20\%$.

---

## 4. State Vector Definitions

### 4.1 Uncontrollable Disturbance Vector ($x_{\text{mat}} \in \mathbb{R}^4$)
Measured properties of the incoming material batch and plant environment:

| Variable | Symbol | Dimension / Units | Nominal Value | Training Range $[x_{\min}, x_{\max}]$ | Physical Significance |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Moisture Content** | $M$ | $\text{wt } \%$ | $0.15\%$ | $[0.05\%, 0.50\%]$ | High moisture causes steam voids and hydrolytic chain scission. |
| **Melt Flow Index** | $\text{MFI}$ | $\text{g}/10\text{ min}$ | $22.0$ | $[14.0, 30.0]$ | Inversely proportional to molecular weight and melt viscosity. |
| **Ambient Intake Temp** | $T_{\text{amb}}$ | $^\circ\text{C}$ | $24.0$ | $[16.0, 32.0]$ | Affects initial thermal gradient and cooling heat transfer rate. |
| **Recycled Content** | $C_{\text{rec}}$ | $\text{wt } \%$ | $25.0\%$ | $[10.0\%, 40.0\%]$ | Influences matrix stiffness and heat capacity of the blend. |

### 4.2 Controllable Machine Parameter Vector ($u \in \mathbb{R}^3$)
Actuators tuned by the fixed SOP or the adaptive AI controller:

| Parameter | Symbol | Dimension / Units | Nominal (SOP) | Operational Bounds $[u_{\min}, u_{\max}]$ | Actuator Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Melt Temperature** | $T_{\text{melt}}$ | $^\circ\text{C}$ | $230.0$ | $[205.0, 255.0]$ | Barrel heater zone temperature setpoint. |
| **Injection Pressure** | $P_{\text{inj}}$ | $\text{MPa}$ | $100.0$ | $[65.0, 145.0]$ | Cavity injection packing and hold pressure. |
| **Cooling Time** | $t_{\text{cool}}$ | $\text{s}$ | $20.0$ | $[12.0, 32.0]$ | In-mold cooling dwell time before part ejection. |

### 4.3 Quality Outcome Vector ($y \in \mathbb{R}^3$)

| Metric | Symbol | Units | Ideal Target | In-Spec Tolerance Band | Engineering Role |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Tensile Yield Strength** | $S$ | $\text{MPa}$ | $S^* = 52.0$ | $[49.0, 55.0]$ | Primary mechanical structural target. Part fails if $< 49.0\text{ MPa}$. |
| **Volumetric Shrinkage** | $V_{\text{sh}}$ | $\%$ | $V_{\text{sh}}^* = 1.20\%$ | $[0.80\%, 1.60\%]$ | Dimensional stability target. Warpage / sink marks if violated. |
| **Specific Energy Consumption** | $E_{\text{proc}}$ | $\text{kWh/cycle}$ | Minimize | $E_{\text{proc}} \le 4.20$ | Process operational cost and sustainability penalty. |

---

## 5. Mathematical Governing Equations

The true simulated process is governed by the vector function:
$$y = f_{\text{true}}(x_{\text{mat}}, u) + \epsilon, \quad \epsilon \sim \mathcal{N}(0, \Sigma)$$

### 5.1 Tensile Yield Strength Formulation ($S$)

Tensile strength is modeled through baseline material fusion, thermal degradation curvature, packing pressure densification, moisture void penalties, cooling dwell crystallization, and non-linear temperature-viscosity interaction:

$$S = S_{\text{base}} + \Delta S_{\text{therm}}(T_{\text{melt}}) + \Delta S_{\text{press}}(P_{\text{inj}}) - \Delta S_{\text{moist}}(M) - \Delta S_{\text{cool}}(t_{\text{cool}}) - \Delta S_{\text{rec}}(C_{\text{rec}}) + \Delta S_{\text{int}}(T_{\text{melt}}, \text{MFI}) + \epsilon_S$$

Where the individual physical components are:
1. **Thermal Fusion and Degradation:**
   $$\Delta S_{\text{therm}}(T_{\text{melt}}) = \beta_T (T_{\text{melt}} - T_0) - \gamma_T (T_{\text{melt}} - T_0)^2$$
   - Captures optimal fusion around $T_0 = 230^\circ\text{C}$. Temperatures below $215^\circ\text{C}$ cause un-melted granules (poor fusion), while temperatures above $245^\circ\text{C}$ induce thermal degradation and chain scission.
2. **Pressure Densification:**
   $$\Delta S_{\text{press}}(P_{\text{inj}}) = \beta_P \ln\left(\frac{P_{\text{inj}}}{P_0}\right)$$
   - Logarithmic pressure compaction according to standard polymer PVT compressibility.
3. **Moisture Void Penalty:**
   $$\Delta S_{\text{moist}}(M) = \lambda_M (M)^{\alpha_M}$$
   - Non-linear sub-exponential void growth. High moisture vaporizes in the barrel, creating internal micro-voids.
4. **Cooling Crystallization Penalty:**
   $$\Delta S_{\text{cool}}(t_{\text{cool}}) = \kappa_{\text{cool}} \left(\frac{t_{\text{cool}} - t_0}{t_0}\right)^2 \cdot \mathbb{I}(t_{\text{cool}} < t_0)$$
   - Premature ejection before gate freeze prevents full crystalline lamellae formation.
5. **Recycled Content Penalty:**
   $$\Delta S_{\text{rec}}(C_{\text{rec}}) = \theta_{\text{rec}} (C_{\text{rec}} - C_0)$$
   - Linear reduction in matrix strength due to accumulated shear history in regrind material.
6. **Temperature-MFI Interaction:**
   $$\Delta S_{\text{int}}(T_{\text{melt}}, \text{MFI}) = \kappa_{\text{int}} \left(\frac{T_{\text{melt}} - T_0}{T_{\text{span}}}\right) \left(\frac{\text{MFI}_0 - \text{MFI}}{\text{MFI}_{\text{span}}}\right)$$
   - Non-linear interaction: When incoming batch has high viscosity (low MFI), raising temperature aids cavity packing; when batch has low viscosity (high MFI), high temperature causes flashing.

### 5.2 Volumetric Shrinkage Formulation ($V_{\text{sh}}$)

Volumetric shrinkage occurs due to thermal contraction upon solidification, opposed by packing pressure compaction and asymptotic cooling stabilization:

$$V_{\text{sh}} = V_0 + \alpha_V (T_{\text{melt}} - T_0) - \beta_V \left(\frac{P_{\text{inj}} - P_0}{P_0}\right) + \gamma_V \exp\left(-\frac{t_{\text{cool}}}{\tau_{\text{cool}}}\right) + \delta_M (M - M_0) - \eta_{\text{rec}} (C_{\text{rec}} - C_0) + \epsilon_V$$

Where:
- $\alpha_V$: Coefficient of thermal expansion contribution.
- $\beta_V$: Packing compaction effect counteracting shrinkage.
- $\gamma_V \exp(-t_{\text{cool}} / \tau_{\text{cool}})$: Transient shrinkage decay reflecting in-mold thermal stabilization.
- $\delta_M$: Volatile moisture expansion causing irregular shrinkage.
- $\eta_{\text{rec}}$: Recycled filler stiffening effect slightly reducing thermal shrinkage.

### 5.3 Specific Process Energy Formulation ($E_{\text{proc}}$)

Represents total energy consumption per injection cycle:

$$E_{\text{proc}} = E_0 + c_{\text{thermal}} (T_{\text{melt}} - T_{\text{amb}}) + c_{\text{hydraulic}} \left(\frac{P_{\text{inj}}}{P_0}\right) + c_{\text{dwell}} t_{\text{cool}}$$

Where:
- $E_0$: Base machine standby energy.
- $c_{\text{thermal}}$: Barrel heater band electrical power required to maintain temperature gradient over ambient.
- $c_{\text{hydraulic}}$: Hydraulic pump / servo-electric motor injection work.
- $c_{\text{dwell}}$: Chiller and clamping holding power per second of cycle dwell.

---

## 6. Calibrated Coefficients, Units, and Rationales

| Coefficient | Symbol | Value | Units | Physical / Empirical Rationale |
| :--- | :---: | :---: | :---: | :--- |
| **Base Tensile Strength** | $S_{\text{base}}$ | $53.5$ | $\text{MPa}$ | Nominal polymer tensile yield strength under ideal processing. |
| **Reference Melt Temp** | $T_0$ | $230.0$ | $^\circ\text{C}$ | Industry-standard operating temperature for polypropylene/polyethylene blends. |
| **Thermal Linear Sensitivity** | $\beta_T$ | $0.06$ | $\text{MPa}/^\circ\text{C}$ | Modest strength improvement with temperature up to optimum. |
| **Thermal Degradation Curvature** | $\gamma_T$ | $0.0035$ | $\text{MPa}/(^\circ\text{C})^2$ | Enforces parabolic drop-off; penalizes thermal over-exposure ($>245^\circ\text{C}$). |
| **Reference Pressure** | $P_0$ | $100.0$ | $\text{MPa}$ | Nominal injection hold pressure. |
| **Pressure Compaction Gain** | $\beta_P$ | $4.50$ | $\text{MPa}$ | Logarithmic strength gain via void compaction and core density. |
| **Moisture Exponent** | $\alpha_M$ | $1.40$ | Dimensionless | Super-linear void coalescence at elevated moisture levels. |
| **Moisture Penalty Scale** | $\lambda_M$ | $14.0$ | $\text{MPa}/(\%)^{1.4}$ | Calibrated so $M=0.45\%$ drops tensile strength by $\approx 4.6\text{ MPa}$, creating defect. |
| **Reference Cooling Time** | $t_0$ | $20.0$ | $\text{s}$ | Nominal dwell time for $3\text{ mm}$ wall thickness. |
| **Cooling Penalty Scale** | $\kappa_{\text{cool}}$ | $2.50$ | $\text{MPa}$ | Penalizes premature demolding ($t_{\text{cool}} < 20\text{ s}$). |
| **Reference Recycled Content** | $C_0$ | $25.0$ | $\text{wt } \%$ | Nominal blend composition. |
| **Recycled Content Penalty** | $\theta_{\text{rec}}$ | $0.08$ | $\text{MPa}/\%$ | Empirical strength degradation with repeated thermal degradation cycles. |
| **Reference MFI** | $\text{MFI}_0$ | $22.0$ | $\text{g}/10\text{ min}$ | Nominal melt flow index. |
| **Temp Normalizer** | $T_{\text{span}}$ | $25.0$ | $^\circ\text{C}$ | Normalization denominator for interaction term. |
| **MFI Normalizer** | $\text{MFI}_{\text{span}}$ | $8.0$ | $\text{g}/10\text{ min}$ | Normalization denominator for interaction term. |
| **Interaction Coefficient** | $\kappa_{\text{int}}$ | $1.80$ | $\text{MPa}$ | Strength of temperature-viscosity cross-coupling. |
| **Stochastic Strength Noise** | $\sigma_S$ | $0.35$ | $\text{MPa}$ | Real-world process variation (cavity sensor measurement noise). |
| **Base Volumetric Shrinkage** | $V_0$ | $1.15$ | $\%$ | Nominal polymer shrinkage rate. |
| **Thermal Expansion Sensitivity** | $\alpha_V$ | $0.008$ | $\% / ^\circ\text{C}$ | Higher melt temperatures expand specific volume. |
| **Pressure Shrinkage Factor** | $\beta_V$ | $0.45$ | $\%$ | Higher packing pressure counteracts volumetric contraction. |
| **Cooling Transient Shrinkage** | $\gamma_V$ | $1.20$ | $\%$ | Amplitude of un-stabilized shrinkage component. |
| **Cooling Time Constant** | $\tau_{\text{cool}}$ | $8.0$ | $\text{s}$ | Exponential relaxation time for part thermal equilibrium. |
| **Reference Moisture** | $M_0$ | $0.15$ | $\text{wt } \%$ | Baseline moisture level. |
| **Moisture Expansion Factor** | $\delta_M$ | $0.60$ | $\% / \%$ | Volatilization expansion causing erratic dimensional variation. |
| **Recycled Filler Factor** | $\eta_{\text{rec}}$ | $0.005$ | $\% / \%$ | Higher particulate fraction slightly restrains dimensional expansion. |
| **Stochastic Shrinkage Noise** | $\sigma_V$ | $0.035$ | $\%$ | Process repeatability noise. |
| **Base Energy** | $E_0$ | $0.20$ | $\text{kWh}$ | Base machine control and standby energy. |
| **Thermal Energy Coefficient** | $c_{\text{thermal}}$ | $0.008$ | $\text{kWh}/^\circ\text{C}$ | Energy required to elevate barrel temperature over factory ambient. |
| **Hydraulic Energy Coefficient** | $c_{\text{hydraulic}}$ | $0.90$ | $\text{kWh}$ | Power drawn by hydraulic/electric screw drives during injection. |
| **Dwell Energy Coefficient** | $c_{\text{dwell}}$ | $0.030$ | $\text{kWh/s}$ | Holding energy per second of cooling time. |

---

## 7. Multi-Objective Adaptive Optimization Formulation

Given an observed material condition $x_{\text{mat}} = [M, \text{MFI}, T_{\text{amb}}, C_{\text{rec}}]$, the adaptive controller finds optimal settings $u^* = [T_{\text{melt}}, P_{\text{inj}}, t_{\text{cool}}]^T$ by solving:

$$\min_{u \in \mathcal{U}} \mathcal{J}(u; x_{\text{mat}}) = w_1 \left(\frac{\hat{S}(x_{\text{mat}}, u) - S^*}{\Delta S_{\text{tol}}}\right)^2 + w_2 \left(\frac{\hat{V}_{\text{sh}}(x_{\text{mat}}, u) - V_{\text{sh}}^*}{\Delta V_{\text{tol}}}\right)^2 + w_3 \left(\frac{\hat{E}_{\text{proc}}(u; x_{\text{mat}})}{E_{\text{nom}}}\right) + \Phi_{\text{pen}}(u; x_{\text{mat}})$$

### 7.1 Weight Vector & Normalizers
- $w_1 = 0.50$ (Tensile Strength fidelity weight)
- $w_2 = 0.35$ (Shrinkage dimensional stability weight)
- $w_3 = 0.15$ (Energy operational cost weight)
- $\Delta S_{\text{tol}} = 3.0\text{ MPa}$ (Half-width of $[49.0, 55.0]$)
- $\Delta V_{\text{tol}} = 0.40\%$ (Half-width of $[0.80, 1.60]\%$)
- $E_{\text{nom}} = 3.15\text{ kWh}$ (Nominal process energy)

### 7.2 Constraints & Infeasibility Handling
1. **Hard Operational Bounds:**
   $$205.0 \le T_{\text{melt}} \le 255.0^\circ\text{C}$$
   $$65.0 \le P_{\text{inj}} \le 145.0\text{ MPa}$$
   $$12.0 \le t_{\text{cool}} \le 32.0\text{ s}$$
2. **Soft Quality Boundary Penalties ($\Phi_{\text{pen}}$):**
   If predicted $\hat{S} < 49.0\text{ MPa}$ or $\hat{V}_{\text{sh}} \notin [0.80, 1.60]\%$, a quadratic barrier penalty is applied:
   $$\Phi_{\text{pen}} = 100.0 \cdot \left(\max(0, 49.0 - \hat{S})\right)^2 + 100.0 \cdot \left(\max(0, \hat{V}_{\text{sh}} - 1.60) + \max(0, 0.80 - \hat{V}_{\text{sh}})\right)^2$$
3. **Infeasibility Handling:**
   When incoming feedstock is extremely degraded ($M > 0.65\%$), the quality target **cannot be met** within machine operational limits. In this event:
   - The optimizer clamps to the Pareto-best feasible setting (maximizing tensile recovery without exceeding pressure limits).
   - An explicit `TargetInfeasibleWarning` flag is returned.
   - The cycle is logged as an unavoidable defect, verifying that our system does not assume impossible targets can be magically achieved.
