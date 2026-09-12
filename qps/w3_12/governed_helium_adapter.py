#!/usr/bin/env python3
"""QPS M01 governed helium provider-selection and canonical HEPAK receipt intake.

No HEPAK values are embedded here. The canonical numeric authority packet is
produced by the child `GBOGEB/cryoplant-project` HEPAK Excel exporter. This
module validates that packet and normalizes it for the CoolProp-side authority
gate. Legacy JSON receipts remain readable for backward compatibility only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

GOVERNING_MIN_K = 2.0
GOVERNING_MAX_K = 4.5

CANONICAL_PRODUCER_REPO = "GBOGEB/cryoplant-project"
CANONICAL_SCHEMA = "qps-hepak-lowt-grid-receipt/v1"
CANONICAL_EXPORTER_BLOB = "a2edd2f730a88b35176dea0e6be39937e159f4d7"
CANONICAL_VALIDATOR_BLOB = "0a7bbfdd2bd2a83403dd82bb4da34a3d0eacdb3e"
CANONICAL_SOLVE_POLICY = "H_FIRST_S_SECOND_TP_SOURCE_BOUND_DENSITY_LAST"
CANONICAL_SOLVE_PAIR = "T+P_SOURCE_BOUND"

CANONICAL_STATE_GRID = {
    "A_CONTRACT": (4.5, 300000.0),
    "A_LKT_SELECTED": (4.4, 300000.0),
    "B_OWNER_EXACT_GATE": (3.6, 2200.0),
    "B_CONTRACT_LKT": (3.8, 2600.0),
    "B_LOCAL_2K_26MBAR": (2.0, 2600.0),
    "B_LOCAL_2K_31MBAR": (2.0, 3100.0),
    "LAMBDA_NEAR": (2.1768, 2600.0),
    "NORMAL_BOILING_VALIDATION": (4.222, 101325.0),
}

CANONICAL_NUMERIC_FIELDS = (
    "enthalpy_J_kg",
    "entropy_J_kgK",
    "density_kg_m3",
    "cp_J_kgK",
    "cv_J_kgK",
    "viscosity_Pa_s",
    "thermal_conductivity_W_mK",
)

CANONICAL_ROW_FIELDS = {
    "state_id",
    "temperature_K",
    "pressure_Pa_abs",
    *CANONICAL_NUMERIC_FIELDS,
    "solve_pair_used",
    "provider",
    "provider_version",
    "unit_set",
    "pressure_basis",
    "source_workbook",
    "source_workbook_sha256",
    "execution_utc",
    "runtime_host",
    "receipt_status",
    "row_sha256",
}

LEGACY_REQUIRED_RECEIPT_FIELDS = {
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


def _finite(value: object, *, field: str, state_id: str) -> float:
    try:
        x = float(value)
    except Exception as exc:
        raise ValueError(
            f"canonical HEPAK row {state_id} has non-numeric {field}: {value!r}"
        ) from exc
    if not math.isfinite(x):
        raise ValueError(
            f"canonical HEPAK row {state_id} has non-finite {field}: {value!r}"
        )
    return x


def _resolve_adjacent_csv(manifest_path: Path, csv_path: object) -> Path:
    if not isinstance(csv_path, str) or not csv_path.strip():
        raise ValueError("canonical HEPAK manifest csv_path is missing")
    rel = Path(csv_path)
    if rel.is_absolute():
        raise ValueError("canonical HEPAK manifest csv_path must be relative")
    root = manifest_path.parent.resolve()
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            "canonical HEPAK manifest csv_path escapes its receipt directory"
        ) from exc
    if not candidate.is_file():
        raise ValueError(f"canonical HEPAK CSV is missing: {candidate}")
    return candidate


def _load_canonical_hepak_receipt(
    manifest_path: Path, payload: Mapping[str, Any]
) -> dict[str, Any]:
    if payload.get("status") != "PASS":
        raise ValueError("canonical HEPAK manifest status must be PASS")
    if payload.get("provider") != "HEPAK":
        raise ValueError("canonical HEPAK manifest provider must be HEPAK")
    if not payload.get("provider_version"):
        raise ValueError("canonical HEPAK manifest provider_version is missing")
    if payload.get("unit_set") != 1:
        raise ValueError("canonical HEPAK manifest must use unit_set 1")
    if payload.get("pressure_basis") != "ABSOLUTE_PA":
        raise ValueError(
            "canonical HEPAK manifest must use ABSOLUTE_PA pressure basis"
        )
    if payload.get("solve_policy") != CANONICAL_SOLVE_POLICY:
        raise ValueError(
            "canonical HEPAK manifest solve policy does not match the governed contract"
        )
    if not payload.get("source_workbook") or not payload.get(
        "source_workbook_sha256"
    ):
        raise ValueError(
            "canonical HEPAK manifest source workbook identity is incomplete"
        )
    if not payload.get("execution_utc") or not payload.get("runtime_host"):
        raise ValueError("canonical HEPAK manifest execution provenance is incomplete")

    expected_ids = set(CANONICAL_STATE_GRID)
    manifest_ids = payload.get("state_ids")
    if not isinstance(manifest_ids, list) or set(manifest_ids) != expected_ids:
        raise ValueError(
            "canonical HEPAK manifest state_ids mismatch: "
            f"expected {sorted(expected_ids)}, got {manifest_ids!r}"
        )
    if payload.get("row_count") != len(expected_ids):
        raise ValueError(
            "canonical HEPAK manifest row_count does not match the governed state grid"
        )

    csv_path = _resolve_adjacent_csv(manifest_path, payload.get("csv_path"))
    actual_csv_sha = _sha256(csv_path)
    if payload.get("csv_sha256") != actual_csv_sha:
        raise ValueError("canonical HEPAK CSV SHA256 does not match the manifest")

    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not CANONICAL_ROW_FIELDS.issubset(
            reader.fieldnames
        ):
            missing = sorted(CANONICAL_ROW_FIELDS - set(reader.fieldnames or []))
            raise ValueError(f"canonical HEPAK CSV missing fields: {missing}")
        rows = list(reader)

    if len(rows) != len(expected_ids):
        raise ValueError(
            "canonical HEPAK CSV row count does not match the governed state grid"
        )

    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        state_id = row.get("state_id", "")
        if state_id not in CANONICAL_STATE_GRID:
            raise ValueError(
                f"canonical HEPAK CSV contains unexpected state_id: {state_id!r}"
            )
        if state_id in by_id:
            raise ValueError(
                f"canonical HEPAK CSV contains duplicate state_id: {state_id}"
            )
        expected_t, expected_p = CANONICAL_STATE_GRID[state_id]
        t = _finite(
            row.get("temperature_K"), field="temperature_K", state_id=state_id
        )
        p = _finite(
            row.get("pressure_Pa_abs"), field="pressure_Pa_abs", state_id=state_id
        )
        if abs(t - expected_t) > 1e-9 or abs(p - expected_p) > 1e-6:
            raise ValueError(
                f"canonical HEPAK state {state_id} coordinates mismatch: "
                f"{(t, p)} != {(expected_t, expected_p)}"
            )
        for field in CANONICAL_NUMERIC_FIELDS:
            _finite(row.get(field), field=field, state_id=state_id)
        if row.get("solve_pair_used") != CANONICAL_SOLVE_PAIR:
            raise ValueError(
                f"canonical HEPAK state {state_id} solve_pair_used is not source-bound T+P"
            )
        if row.get("provider") != "HEPAK" or row.get("provider_version") != str(
            payload["provider_version"]
        ):
            raise ValueError(
                f"canonical HEPAK state {state_id} provider identity mismatch"
            )
        if row.get("unit_set") != "1" or row.get("pressure_basis") != "ABSOLUTE_PA":
            raise ValueError(
                f"canonical HEPAK state {state_id} unit/pressure basis mismatch"
            )
        if row.get("source_workbook") != str(payload["source_workbook"]):
            raise ValueError(
                f"canonical HEPAK state {state_id} source workbook mismatch"
            )
        if row.get("source_workbook_sha256") != str(
            payload["source_workbook_sha256"]
        ):
            raise ValueError(
                f"canonical HEPAK state {state_id} source workbook SHA mismatch"
            )
        if row.get("execution_utc") != str(payload["execution_utc"]):
            raise ValueError(
                f"canonical HEPAK state {state_id} execution timestamp mismatch"
            )
        if row.get("runtime_host") != str(payload["runtime_host"]):
            raise ValueError(f"canonical HEPAK state {state_id} runtime host mismatch")
        if row.get("receipt_status") != "PASS":
            raise ValueError(f"canonical HEPAK state {state_id} is not PASS")
        if len(row.get("row_sha256", "")) != 64:
            raise ValueError(
                f"canonical HEPAK state {state_id} row_sha256 is missing or malformed"
            )
        by_id[state_id] = dict(row)

    if set(by_id) != expected_ids:
        raise ValueError(
            "canonical HEPAK CSV does not contain the complete governed state grid"
        )

    return {
        "provider_HEPAK": True,
        "provider_version": str(payload["provider_version"]),
        "runtime_or_workbook_identity": str(payload["source_workbook"]),
        "unit_set": 1,
        "pressure_basis_absolute": True,
        "execution_date": str(payload["execution_utc"]),
        "input_sha256": str(payload["source_workbook_sha256"]),
        "output_sha256": actual_csv_sha,
        "receipt_file_sha256": _sha256(manifest_path),
        "canonical_schema": CANONICAL_SCHEMA,
        "canonical_producer_repo": CANONICAL_PRODUCER_REPO,
        "canonical_exporter_blob": CANONICAL_EXPORTER_BLOB,
        "canonical_validator_blob": CANONICAL_VALIDATOR_BLOB,
        "canonical_csv_path": str(csv_path),
        "canonical_state_ids": sorted(by_id),
        "canonical_rows": by_id,
        "runtime_host": str(payload["runtime_host"]),
        "authority_transfer": False,
    }


def _load_legacy_hepak_receipt(
    receipt_path: Path, payload: dict[str, Any]
) -> dict[str, Any]:
    missing = sorted(LEGACY_REQUIRED_RECEIPT_FIELDS - set(payload))
    if missing:
        raise ValueError(f"HEPAK receipt missing required provenance fields: {missing}")
    if not payload.get("provider_HEPAK"):
        raise ValueError("HEPAK receipt does not identify HEPAK as provider")
    if payload.get("pressure_basis_absolute") is not True:
        raise ValueError("HEPAK receipt must explicitly use absolute pressure")
    payload = dict(payload)
    payload["receipt_file_sha256"] = _sha256(receipt_path)
    payload["authority_transfer"] = False
    return payload


def load_hepak_receipt(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    receipt_path = Path(path)
    if not receipt_path.is_file():
        return None
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    if payload.get("schema") == CANONICAL_SCHEMA:
        return _load_canonical_hepak_receipt(receipt_path, payload)
    return _load_legacy_hepak_receipt(receipt_path, payload)


def provider_decision(
    T_K: float, *, hepak_receipt: Mapping[str, Any] | None = None
) -> dict[str, Any]:
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
