#!/usr/bin/env python3
"""Execute the W3-12 HEPAK authority challenge without inventing licensed data."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from governed_helium_adapter import load_hepak_receipt, provider_decision

EXACT_STATES = {
    "A": {"T_K": 4.5, "P_Pa_abs": 300000},
    "B_LKT": {"T_K": 3.6, "P_Pa_abs": 2200},
    "B_ALAT": {"T_K": 3.8, "P_Pa_abs": 2600},
    "B_QRB_27mbar": {"T_K": 2.0, "P_Pa_abs": 2700},
    "B_QCELL_31mbar": {"T_K": 2.0, "P_Pa_abs": 3100},
    "LAMBDA_NEAR": {"T_K": 2.1768, "P_Pa_abs": 2600},
}

ap = argparse.ArgumentParser()
ap.add_argument("--hepak-receipt")
ap.add_argument("--source-sha", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

receipt = load_hepak_receipt(a.hepak_receipt)
decisions = {
    name: provider_decision(state["T_K"], hepak_receipt=receipt)
    for name, state in EXACT_STATES.items()
}
held = [name for name, d in decisions.items() if d["status"] == "HOLD"]

# Guard against the exact governance failure W3-12 is meant to prevent.
if receipt is None:
    if sorted(held) != sorted(EXACT_STATES):
        raise AssertionError(("missing HEPAK receipt must hold every 2.0-4.5 K challenge state", decisions))
    # Outside the mandatory band CoolProp may execute, but this is not a transfer
    # of QPLANT engineering authority.
    outside = provider_decision(10.0, hepak_receipt=None)
    if outside["provider"] != "CoolProp" or outside["governing"] is not False:
        raise AssertionError(outside)

status = "REFERENCE_READY" if receipt is not None else "HEPAK_2K_CROSSCHECK_REQUIRED"
outcome = "READY_FOR_REFERENCE_COMPARISON" if receipt is not None else "HOLD_EXTERNAL_LICENSED_NUMERIC_INPUT"
result = {
    "schema": "qps-w3-12-hepak-authority-challenge/v1",
    "observed_at": datetime.now(timezone.utc).isoformat(),
    "repo": "GBOGEB/CoolProp",
    "source_sha": a.source_sha,
    "execution": {
        "steps_gt0": True,
        "workflow_run_id": os.getenv("GITHUB_RUN_ID", "UNBOUND"),
        "outcome": outcome,
    },
    "reference_challenge": {
        "independent_reference": "NIST_TN1334_validation_only",
        "exact_states": EXACT_STATES,
        "provider_decisions": decisions,
        "status": status,
    },
    "governed_adapter": {
        "implemented": True,
        "mandatory_hepak_band_K": [2.0, 4.5],
        "runtime_without_receipt_refuses_governing_value": True,
    },
    "licensed_hepak_numeric_receipt_present": receipt is not None,
    "external_consumer_authority_ready": receipt is not None,
    "dov2_promoted": False,
    "authority_transfer": False,
    "first_red": None if receipt is not None else "MISSING_EXACT_LICENSED_HEPAK_NUMERIC_RECEIPT",
}

out = Path(a.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
