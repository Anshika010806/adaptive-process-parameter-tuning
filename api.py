
from __future__ import annotations

import os
import time
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict

from src.optimization.adaptive_tuner import AdaptiveProcessTuner


ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models" / "surrogate_randomforest.joblib"

tuner: Optional[AdaptiveProcessTuner] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global tuner

    if not MODEL_PATH.is_file():
        raise RuntimeError(f"Saved surrogate model not found: {MODEL_PATH}")

    model = joblib.load(MODEL_PATH)
    tuner = AdaptiveProcessTuner(surrogate_pipeline=model)

    yield

    tuner = None


app = FastAPI(
    title="Adaptive Process Parameter Tuning API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "https://adaptive-process-parameter-tuning.vercel.app",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class MaterialInputs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    moisture_pct: float
    melt_flow_index: float
    ambient_temp_c: float
    recycled_pct: float


def finite_or_none(value: float) -> Optional[float]:
    """Prevent NaN and Infinity from entering JSON responses."""
    result = float(value)
    return result if np.isfinite(result) else None


@app.get("/health")
def health():
    return {
        "status": "ONLINE",
        "mode": "FASTAPI_REST",
        "model": "RandomForest",
    }


@app.post("/api/tune")
def tune(inputs: MaterialInputs):
    if tuner is None:
        raise HTTPException(status_code=503, detail="Optimizer is not initialized")

    started = time.perf_counter()

    try:
        result = tuner.optimize_cycle(
            moisture_pct=inputs.moisture_pct,
            melt_flow_index=inputs.melt_flow_index,
            ambient_temp_c=inputs.ambient_temp_c,
            recycled_pct=inputs.recycled_pct,
        )

        guard = tuner.domain_guard.validate_material(
            moisture_pct=inputs.moisture_pct,
            melt_flow_index=inputs.melt_flow_index,
            ambient_temp_c=inputs.ambient_temp_c,
            recycled_pct=inputs.recycled_pct,
        )

        baseline_energy = float(
            tuner.compute_energy(
                tuner.sop_defaults["melt_temp_c"],
                tuner.sop_defaults["injection_pressure_mpa"],
                tuner.sop_defaults["cooling_time_s"],
                inputs.ambient_temp_c,
            )
        )

        if baseline_energy > 0 and result.is_feasible:
            savings_pct = (
                (baseline_energy - result.predicted_energy_kwh)
                / baseline_energy
            ) * 100.0
        else:
            savings_pct = 0.0

        guard_status = {
            "VALID": "VALID",
            "INVALID_INPUT": "INVALID_INPUT",
            "OOD_REJECTED": "OOD_REJECTED",
            "INFEASIBLE": "UNCOMPENSABLE",
            "OOD_WARNING": "OOD_REJECTED",
        }.get(guard.status, "INVALID_INPUT")

        # Preserve the optimizer's actual status, including SUBOPTIMAL.
        api_status = result.status

        return {
            "status": api_status,
            "parameters": {
                "melt_temp_c": result.melt_temp_c,
                "injection_pressure_mpa": result.injection_pressure_mpa,
                "cooling_time_s": result.cooling_time_s,
            },
            "predicted_tensile_mpa": finite_or_none(
                result.predicted_tensile_mpa
            ),
            "predicted_shrinkage_pct": finite_or_none(
                result.predicted_shrinkage_pct
            ),
            "predicted_energy_kwh": finite_or_none(
                result.predicted_energy_kwh
            ),
            "energy_savings_pct": finite_or_none(savings_pct),
            "safety_margin_S": finite_or_none(
                tuner.get_tensile_safety_margin(inputs.recycled_pct)
            ),
            "guard_result": {
                "is_valid": guard.is_valid,
                "status": guard_status,
                "rejection_reason": (
                    guard.message if not guard.is_feasible else None
                ),
                "violating_fields": guard.violations,
            },
            "execution_latency_ms": (
                time.perf_counter() - started
            ) * 1000.0,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        # Keep detailed exceptions in server logs, not in public responses.
        print(f"Tuning request failed: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Tuning failed due to an internal server error.",
        ) from exc
