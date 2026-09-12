#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from governed_helium_adapter import (
    CANONICAL_NUMERIC_FIELDS,
    CANONICAL_SOLVE_PAIR,
    CANONICAL_SOLVE_POLICY,
    CANONICAL_STATE_GRID,
    load_hepak_receipt,
    provider_decision,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CanonicalHepakReceiptTests(unittest.TestCase):
    def make_packet(self, root: Path):
        csv_path = root / "he_reference_hepak_lowT_grid.csv"
        fieldnames = [
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
        ]
        rows = []
        for i, (state_id, (t, p)) in enumerate(CANONICAL_STATE_GRID.items(), start=1):
            row = {
                "state_id": state_id,
                "temperature_K": t,
                "pressure_Pa_abs": p,
                "solve_pair_used": CANONICAL_SOLVE_PAIR,
                "provider": "HEPAK",
                "provider_version": "3.4",
                "unit_set": "1",
                "pressure_basis": "ABSOLUTE_PA",
                "source_workbook": "CH15_HEPAK_QPLANT_Runtime_v0_1.xlsx",
                "source_workbook_sha256": "a" * 64,
                "execution_utc": "2026-09-12T10:00:00+00:00",
                "runtime_host": "LICENSED-WINDOWS-HOST",
                "receipt_status": "PASS",
                "row_sha256": f"{i:064x}",
            }
            for j, field in enumerate(CANONICAL_NUMERIC_FIELDS, start=1):
                row[field] = float(i * 100 + j)
            rows.append(row)
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        manifest = {
            "schema": "qps-hepak-lowt-grid-receipt/v1",
            "status": "PASS",
            "csv_path": csv_path.name,
            "csv_sha256": sha256(csv_path),
            "source_workbook": "CH15_HEPAK_QPLANT_Runtime_v0_1.xlsx",
            "source_workbook_sha256": "a" * 64,
            "provider": "HEPAK",
            "provider_version": "3.4",
            "unit_set": 1,
            "pressure_basis": "ABSOLUTE_PA",
            "execution_utc": "2026-09-12T10:00:00+00:00",
            "runtime_host": "LICENSED-WINDOWS-HOST",
            "row_count": len(rows),
            "state_ids": list(CANONICAL_STATE_GRID),
            "solve_policy": CANONICAL_SOLVE_POLICY,
        }
        manifest_path = root / "he_reference_hepak_lowT_grid.csv.manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path, csv_path

    def test_canonical_packet_normalizes_for_governed_adapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path, _ = self.make_packet(Path(tmp))
            receipt = load_hepak_receipt(manifest_path)
            self.assertEqual(
                receipt["canonical_schema"], "qps-hepak-lowt-grid-receipt/v1"
            )
            self.assertEqual(
                set(receipt["canonical_state_ids"]), set(CANONICAL_STATE_GRID)
            )
            self.assertEqual(
                provider_decision(2.0, hepak_receipt=receipt)["provider"], "HEPAK"
            )
            self.assertFalse(receipt["authority_transfer"])

    def test_tampered_csv_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path, csv_path = self.make_packet(Path(tmp))
            csv_path.write_text(
                csv_path.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "CSV SHA256"):
                load_hepak_receipt(manifest_path)

    def test_missing_state_is_rejected_even_with_rehashed_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path, csv_path = self.make_packet(root)
            lines = csv_path.read_text(encoding="utf-8").splitlines()
            csv_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["csv_sha256"] = sha256(csv_path)
            manifest["row_count"] -= 1
            manifest["state_ids"] = manifest["state_ids"][:-1]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "state_ids mismatch"):
                load_hepak_receipt(manifest_path)

    def test_no_receipt_remains_fail_closed(self):
        decision = provider_decision(2.0, hepak_receipt=None)
        self.assertEqual(decision["status"], "HOLD")
        self.assertFalse(decision["governing"])


if __name__ == "__main__":
    unittest.main()
