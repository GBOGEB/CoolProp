#!/usr/bin/env python3
"""QPS M01 governed helium provider-selection gate.

This module does not embed HEPAK data or infer HEPAK authority. It only enforces
provider policy. In the QPLANT 2.0--4.5 K band, a separately supplied exact
licensed HEPAK numeric receipt is mandatory before a property value can be
marked governing.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

GOVERNING_MIN_K = 2.0
GOVERNING_MAX_K = 4.5
REQUIRED_RECEIPT_FIELDS = {
    "provider_HEPAK",
    "provider_version",
    "runtime_or_workbook_identity",
    "unit_set",
    "pressure_basis_absolute",
    "execution_date",
    "input_sha256",
    "output_sha256",
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_hepak_receipt(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    receipt_path = Path(path)
    if not receipt_path.is_file():
        return None
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_RECEIPT_FIELDS - set(payload))
    if missing:
        raise ValueError(f"HEPAK receipt missing required provenance fields: {missing}")
    if not payload.get("provider_HEPAK"):
        raise ValueError("HEPAK receipt does not identify HEPAK as provider")
    if payload.get("pressure_basis_absolute") is not True:
        raise ValueError("HEPAK receipt must explicitly use absolute pressure")
    payload["receipt_file_sha256"] = _sha256(receipt_path)
    return payload


def provider_decision(T_K: float, *, hepak_receipt: Mapping[str, Any] | None = None) -> dict[str, Any]:
    T_K = float(T_K)
    in_governing_band = GOVERNING_MIN_K <= T_K <= GOVERNING_MAX_K
    if in_governing_band:
        if hepak_receipt is None:
            return {
                "status": "HOLD",
                "provider": None,
                "reason": "HEPAK_2K_CROSSCHECK_REQUIRED",
                "governing": False,
                "authority_transfer": False,
            }
        return {
            "status": "READY_FOR_HEPAK_VALUE_LOOKUP",
            "provider": "HEPAK",
            "reason": "LICENSED_HEPAK_RECEIPT_PRESENT",
            "governing": True,
            "authority_transfer": False,
        }
    return {
        "status": "COOLPROP_RUNTIME_ALLOWED",
        "provider": "CoolProp",
        "reason": "OUTSIDE_QPLANT_HEPAK_MANDATORY_BAND",
        "governing": False,
        "authority_transfer": False,
    }
