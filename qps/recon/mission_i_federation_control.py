#!/usr/bin/env python3
"""Validate the exact W145 CoolProp -> QPS child -> KEB -> DOW federation chain.

This probe is intentionally read-only and stdlib-only.  It verifies immutable
GitHub blob identities and authority-preserving tokens; it does not promote
CoolProp, KEB or DOW evidence into QPS engineering acceptance.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API_ROOT = "https://api.github.com"
DEFAULT_CONTROL = Path("qps/recon/FEDERATION_CONTROL.json")
DEFAULT_OUTPUT = Path("qps/recon/receipts/mission_i_federation_control.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", type=Path, default=DEFAULT_CONTROL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def api_json(url: str) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "qps-mission-i-federation-control",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_anchor(anchor: dict[str, Any]) -> dict[str, Any]:
    repo = anchor["repo"]
    path = urllib.parse.quote(anchor["path"], safe="/")
    ref = urllib.parse.quote(anchor["ref"], safe="")
    payload = api_json(f"{API_ROOT}/repos/{repo}/contents/{path}?ref={ref}")
    encoded = payload.get("content")
    if not encoded:
        raise RuntimeError(f"{anchor['role']}: GitHub contents response has no content")
    text = base64.b64decode(encoded).decode("utf-8")
    missing_tokens = [token for token in anchor["required_tokens"] if token not in text]
    blob_matches = payload.get("sha") == anchor["blob_sha"]
    return {
        "role": anchor["role"],
        "repo": repo,
        "ref": anchor["ref"],
        "path": anchor["path"],
        "expected_blob_sha": anchor["blob_sha"],
        "observed_blob_sha": payload.get("sha"),
        "blob_matches": blob_matches,
        "required_tokens": len(anchor["required_tokens"]),
        "missing_tokens": missing_tokens,
        "status": "PASS" if blob_matches and not missing_tokens else "RED",
    }


def main() -> int:
    args = parse_args()
    control = json.loads(args.control.read_text(encoding="utf-8"))
    anchors: list[dict[str, Any]] = []
    failures: list[str] = []

    for anchor in control["anchors"]:
        result = fetch_anchor(anchor)
        anchors.append(result)
        if not result["blob_matches"]:
            failures.append(f"FEDERATION_BLOB_DRIFT:{result['role']}")
        elif result["missing_tokens"]:
            failures.append(f"FEDERATION_CONTRACT_DRIFT:{result['role']}")

    promotion = control["promotion"]
    if promotion["static_federation"] != "ACHIEVED":
        failures.append("STATIC_FEDERATION_NOT_ACHIEVED")
    if promotion["engineering_numerical_DOV"] != "WITHHELD_CHILD_GATES":
        failures.append("ENGINEERING_AUTHORITY_BOUNDARY_CHANGED")
    if promotion["formal_engineering_credit_delta"] != 0:
        failures.append("UNAUTHORIZED_ENGINEERING_CREDIT")
    if promotion["formal_SAT_credit_delta"] != 0:
        failures.append("UNAUTHORIZED_SAT_CREDIT")

    receipt = {
        "schema": "qps.mission_i.federation_control_receipt.v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "mission": control["mission"],
        "wave": control["wave"],
        "coolprop_runtime": control["coolprop_runtime"],
        "anchors": anchors,
        "control_invariants": control["control_invariants"],
        "promotion": promotion,
        "summary": {
            "anchors_required": len(anchors),
            "anchors_passed": sum(item["status"] == "PASS" for item in anchors),
            "status": "PASS" if not failures else "RED",
            "first_red": failures[0] if failures else None,
            "failures": failures,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))

    if failures:
        print(f"FIRST_RED={failures[0]}", file=sys.stderr)
        return 2
    print("Mission I federation control PASS: exact W145 child/KEB/DOW anchors remain authority-safe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
