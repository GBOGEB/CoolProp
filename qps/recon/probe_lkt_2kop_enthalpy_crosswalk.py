#!/usr/bin/env python3
"""Exact-source LKT c30 2K-OP A/B/D/E/W CoolProp compatibility crosswalk.

This probe consumes the QPS W142 source-return-complete expected row and emits
thermophysical compatibility diagnostics. It does not define the contractual
4.5 K-equivalent/SAT equal-exergy formula and cannot replace licensed HEPAK at
the governed low-temperature authority gate.
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
from CoolProp.CoolProp import PhaseSI, PropsSI, get_global_param_string

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "qps" / "recon" / "receipts" / "lkt_2kop_enthalpy_crosswalk.json"

SOURCE = {
    "repo": "GBOGEB/cryoplant-project",
    "artifact": "triage/w142/QPS_W142_LKT_C30_2KOP_SELECTED_STREAM_COMPLETE_v0.1.yaml",
    "document": "P230000201_MOL_16_Proposal_Technical_Part_Issue_01",
    "section": "4.1_Guaranteed_and_Expected_Performance",
    "offer_sha256": "8d074db4d07bf6d904635d7666664ebd54a2d0d7fc80d53b8f256be9e48911d0",
    "row": "LKT_expected_selected_row",
    "state": "c30_2K_OP",
}

# Exact current expected row from the controlled W142 child artifact.
POINTS = {
    "A": {"mdot_g_s": 44.0, "T_K": 4.5, "P_Pa": 300000.0},
    "B": {"mdot_g_s": 41.6, "T_K": 3.6, "P_Pa": 2200.0},
    "D": {"mdot_g_s": 81.0, "T_K": 40.0, "P_Pa": 1260000.0},
    "E": {"mdot_g_s": 81.0, "T_K": 60.0, "P_Pa": 1150000.0},
    "W": {"mdot_g_s": 2.42, "T_K": 300.0, "P_Pa": 110000.0},
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def eval_state(name: str, state: dict) -> dict:
    out = {"id": name, **state, "fluid": "HEOS::Helium", "errors": []}
    try:
        out["phase"] = PhaseSI("T", state["T_K"], "P", state["P_Pa"], "HEOS::Helium")
    except Exception as exc:
        out["phase"] = None
        out["errors"].append(f"PhaseSI:{type(exc).__name__}:{exc}")
    for key, prop in {
        "h_J_kg": "Hmass",
        "s_J_kgK": "Smass",
        "rho_kg_m3": "Dmass",
        "cp_J_kgK": "Cpmass",
    }.items():
        try:
            value = float(PropsSI(prop, "T", state["T_K"], "P", state["P_Pa"], "HEOS::Helium"))
            if not math.isfinite(value):
                raise ValueError(f"nonfinite:{value}")
            out[key] = value
        except Exception as exc:
            out[key] = None
            out["errors"].append(f"{prop}:{type(exc).__name__}:{exc}")
    out["status"] = "PASS" if not out["errors"] else "FAIL"
    out["authoritative_for_qps"] = False
    return out


def main() -> int:
    states = {name: eval_state(name, state) for name, state in POINTS.items()}
    first_red = next((name for name, state in states.items() if state["status"] != "PASS"), None)

    diagnostics = {}
    if first_red is None:
        h = {name: state["h_J_kg"] for name, state in states.items()}
        mdot = {name: state["mdot_g_s"] / 1000.0 for name, state in states.items()}

        # A is the incoming cold supply; the expected row closes approximately to B + W.
        mass_residual_g_s = POINTS["A"]["mdot_g_s"] - POINTS["B"]["mdot_g_s"] - POINTS["W"]["mdot_g_s"]
        q_abw_W = mdot["B"] * h["B"] + mdot["W"] * h["W"] - mdot["A"] * h["A"]
        q_de_W = mdot["E"] * h["E"] - mdot["D"] * h["D"]

        diagnostics = {
            "A_to_B_plus_W_mass_balance": {
                "reported_residual_g_s": mass_residual_g_s,
                "residual_fraction_of_A": mass_residual_g_s / POINTS["A"]["mdot_g_s"],
                "classification": "SOURCE_ROUNDING_DIAGNOSTIC_NOT_CORRECTED",
            },
            "raw_boundary_enthalpy_rate": {
                "A_to_B_plus_W_W": q_abw_W,
                "D_to_E_W": q_de_W,
                "sum_W": q_abw_W + q_de_W,
                "classification": "CALCULATED_PHYSICAL_ENTHALPY_FLOW_NOT_4P5K_EQUIVALENT",
            },
            "return_cold_guard": {
                "rule": "If A-to-B/W useful refrigeration is credited across the user boundary, B and W are return states and their residual cold/exergy shall not be credited again as a second exported refrigeration load.",
                "duplicate_credit_allowed": False,
            },
        }

    execution_sha = git("rev-parse", "HEAD")
    receipt = {
        "schema": "qps-coolprop-w145-lkt-2kop-crosswalk/0.1",
        "mission": "W145_NUMERICAL_DOV_ENTHALPY_CROSSWALK",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "execution": {
            "repo": "GBOGEB/CoolProp",
            "sha": execution_sha,
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "python": sys.version,
            "platform": platform.platform(),
        },
        "engine": {
            "name": "CoolProp",
            "version": getattr(CoolProp, "__version__", None),
            "gitrevision": get_global_param_string("gitrevision"),
            "backend": "HEOS",
            "fluid": "Helium",
        },
        "source_binding": SOURCE,
        "states": states,
        "diagnostics": diagnostics,
        "authority": {
            "classification": "COMPATIBILITY_REFERENCE_CALCULATED",
            "engineering_promotion_forbidden": True,
            "licensed_HEPAK_required_for_governed_lowT_authority": True,
            "SAT_equal_exergy_formula_required_from_QPS_issue_1021": True,
            "Qeq_promotion": "WITHHELD",
        },
        "summary": {
            "states_required": 5,
            "states_passed": sum(v["status"] == "PASS" for v in states.values()),
            "first_red": first_red,
            "status": "PASS" if first_red is None else "FAIL",
        },
    }

    canonical = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(canonical, encoding="utf-8")
    print(canonical, end="")
    print(f"receipt_sha256={sha256_bytes(canonical.encode('utf-8'))}")
    return 0 if first_red is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
