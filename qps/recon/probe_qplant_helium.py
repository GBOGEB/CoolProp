#!/usr/bin/env python3
"""QPS DARKLAND CoolProp smoke probe.

This script is intentionally small and evidence-oriented. It exercises the
CoolProp package built from the checked-out repository, captures provenance,
and emits one JSON receipt. A/B/D/W are required to return finite values.
The 2 K point is observational only and is always classified as requiring an
independent HEPAK cross-check before QPS promotion.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import CoolProp
from CoolProp.CoolProp import PhaseSI, PropsSI, get_fluid_param_string, get_global_param_string

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "qps" / "recon" / "receipts" / "coolprop_qplant_helium_smoke.json"

POINTS = [
    {"id": "A", "T_K": 4.5, "P_Pa": 300000.0, "authority": "PROBE"},
    {"id": "B", "T_K": 3.6, "P_Pa": 3000.0, "authority": "PROBE"},
    {"id": "D", "T_K": 40.0, "P_Pa": 1400000.0, "authority": "PROBE"},
    {"id": "W", "T_K": 300.0, "P_Pa": 105000.0, "authority": "PROBE"},
    {"id": "BOUNDARY_2K", "T_K": 2.0, "P_Pa": 3000.0, "authority": "VALIDATION_REQUIRED"},
]

OUTPUTS = {
    "density_kg_m3": "Dmass",
    "enthalpy_J_kg": "Hmass",
    "entropy_J_kgK": "Smass",
    "cp_J_kgK": "Cpmass",
    "viscosity_Pa_s": "VISCOSITY",
    "conductivity_W_mK": "CONDUCTIVITY",
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evaluate_point(point: dict) -> dict:
    result = {**point, "backend": "HEOS", "fluid": "Helium", "outputs": {}, "errors": []}
    try:
        result["phase"] = PhaseSI("T", point["T_K"], "P", point["P_Pa"], "HEOS::Helium")
    except Exception as exc:  # pragma: no cover - evidence capture
        result["phase"] = None
        result["errors"].append(f"PhaseSI: {type(exc).__name__}: {exc}")

    for label, prop in OUTPUTS.items():
        try:
            value = float(PropsSI(prop, "T", point["T_K"], "P", point["P_Pa"], "HEOS::Helium"))
            if not math.isfinite(value):
                raise ValueError(f"non-finite result: {value}")
            result["outputs"][label] = value
        except Exception as exc:  # pragma: no cover - evidence capture
            result["outputs"][label] = None
            result["errors"].append(f"{prop}: {type(exc).__name__}: {exc}")

    if point["id"] == "BOUNDARY_2K":
        result["classification"] = "VALIDATION_REQUIRED"
        result["authoritative_for_qps"] = False
        result["boundary_reason"] = "CoolProp Helium saturation/ancillary data expose a 2.1768 K lower boundary; cross-check HEPAK before promotion."
    elif result["errors"]:
        result["classification"] = "FAIL"
        result["authoritative_for_qps"] = False
    else:
        result["classification"] = "PASS"
        result["authoritative_for_qps"] = False
    return result


def main() -> int:
    execution_sha = git("rev-parse", "HEAD")
    baseline_sha = "a3c743026521ff557f8c2e85701c726898b00e0b"
    helium_model = ROOT / "dev" / "fluids" / "Helium.json"

    points = [evaluate_point(p) for p in POINTS]
    required = [p for p in points if p["id"] in {"A", "B", "D", "W"}]
    first_red = next((p for p in required if p["classification"] != "PASS"), None)

    receipt = {
        "schema": "qps.recon.smoke_receipt.v1",
        "mission_id": "QPS-DARKLAND-RECON-COOLPROP-P1",
        "worker": "Smoker",
        "probe": "qplant_helium_PT_properties",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repo": "GBOGEB/CoolProp",
        "source_baseline_sha": baseline_sha,
        "execution_sha": execution_sha,
        "engine": {
            "name": "CoolProp",
            "package_version": getattr(CoolProp, "__version__", None),
            "package_gitrevision": getattr(CoolProp, "__gitrevision__", None),
            "global_gitrevision": get_global_param_string("gitrevision"),
            "backend": "HEOS",
            "fluid": "Helium",
            "fluid_CAS": get_fluid_param_string("Helium", "CAS"),
            "fluid_model_path": "dev/fluids/Helium.json",
            "fluid_model_sha256": sha256(helium_model),
            "eos_reference": "OrtizVega-JPCRD-2019",
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "runner_os": os.environ.get("RUNNER_OS"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        },
        "points": points,
        "summary": {
            "executed_points": len(points),
            "required_points": len(required),
            "required_passed": sum(p["classification"] == "PASS" for p in required),
            "required_failed": sum(p["classification"] != "PASS" for p in required),
            "validation_required": sum(p["classification"] == "VALIDATION_REQUIRED" for p in points),
            "first_red": None if first_red is None else first_red["id"],
            "status": "PASS" if first_red is None else "FAIL",
        },
        "promotion_boundary": {
            "coolprop_is_not_automatically_authoritative_hepak_replacement_at_2K": True,
            "hepak_crosscheck_required": True,
            "qps_ssot_promotion": "HOLD_PENDING_CROSSCHECK",
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if first_red is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
