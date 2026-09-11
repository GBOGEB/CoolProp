#!/usr/bin/env python3
"""CoolProp thermophysical adapter for the sanitized QPS W111 power/utility lane.

This adapter is a compatibility/reference calculator only. It consumes no bidder
PDF bytes and cannot promote QPS engineering state.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess

from CoolProp.CoolProp import PropsSI
import CoolProp

ROOT = Path(__file__).resolve().parents[2]
RECEIPTS = Path(__file__).resolve().parent / "receipts"
RECEIPTS.mkdir(parents=True, exist_ok=True)
OUT = RECEIPTS / "coolprop_w111_power_utility_thermo.json"

POINT = {
    "id": "LKT_HP_NORMAL_56HZ_EACH",
    "fluid": "Helium",
    "T1_K": 298.0,
    "P1_Pa": 1.05e5,
    "P2_Pa": 14.0e5,
    "mass_flow_kg_s": 0.0815,
    "package_input_kW": 203.5,
    "evidence_class": "OWNER_IMMUTABLE_PLUS_SOURCE_BOUND_DERIVED_EQUAL_SHARE",
}


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = POINT
    fluid = p["fluid"]
    T1 = p["T1_K"]
    P1 = p["P1_Pa"]
    P2 = p["P2_Pa"]
    mdot = p["mass_flow_kg_s"]

    h1 = PropsSI("H", "T", T1, "P", P1, fluid)
    s1 = PropsSI("S", "T", T1, "P", P1, fluid)
    rho1 = PropsSI("D", "T", T1, "P", P1, fluid)
    cp1 = PropsSI("Cpmass", "T", T1, "P", P1, fluid)
    cv1 = PropsSI("Cvmass", "T", T1, "P", P1, fluid)
    h2s = PropsSI("H", "P", P2, "S", s1, fluid)
    T2s = PropsSI("T", "P", P2, "S", s1, fluid)

    isentropic_kW = mdot * (h2s - h1) / 1000.0
    R_specific = cp1 - cv1
    isothermal_kW = mdot * R_specific * T1 * math.log(P2 / P1) / 1000.0
    package_eta_iso = isothermal_kW / p["package_input_kW"]
    apparent_eta_is = isentropic_kW / p["package_input_kW"]

    receipt = {
        "schema": "qps-coolprop-w111-power-utility-thermo/0.1",
        "repo": "GBOGEB/CoolProp",
        "authority_scope": "COMPATIBILITY_REFERENCE",
        "engineering_promotion_forbidden": True,
        "qps_child_authority": {
            "repo": "GBOGEB/cryoplant-project",
            "source_ssot": "ocd-adr/20_canonical/control/QPS_W111_POWER_UTILITY_SOURCE_SSOT_v1.json",
            "source_ssot_git_blob_sha": "d19975a150a3530cc4db3bd2fbbf4180f757c2a4",
        },
        "consumer": "GBOGEB/ABACUS",
        "coolprop": {"version": CoolProp.__version__, "git_head": git_head(), "backend": "HEOS", "fluid": fluid},
        "input": p,
        "state_1": {"h_J_kg": h1, "s_J_kgK": s1, "rho_kg_m3": rho1, "cp_J_kgK": cp1, "cv_J_kgK": cv1, "R_effective_J_kgK": R_specific},
        "isentropic_reference": {"h2s_J_kg": h2s, "T2s_K": T2s, "ideal_power_kW": isentropic_kW, "apparent_efficiency_vs_package": apparent_eta_is, "classification": "REFERENCE_ONLY_FOR_INTERCOOLED_PACKAGE"},
        "isothermal_reference": {"ideal_power_kW": isothermal_kW, "package_isothermal_efficiency": package_eta_iso},
        "guards": [
            "CoolProp_receipt_does_not_replace_HEPAK_or_bidder_guarantee",
            "full_1p05_to_14_bara_isentropic_reference_is_not_whole_intercooled_package_efficiency",
            "no_raw_bidder_offer_ingestion",
            "QPS_engineering_promotion_requires_child_reentry",
        ],
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    digest = sha256(OUT)
    print("QPS_COOLPROP_W111_POWER_UTILITY=PASS")
    print(f"receipt={OUT}")
    print(f"sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
