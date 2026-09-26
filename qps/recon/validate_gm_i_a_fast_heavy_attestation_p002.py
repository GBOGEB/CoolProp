#!/usr/bin/env python3
import json
from pathlib import Path

P = Path(__file__).resolve().parent / "federation" / "GM_I_A_FAST_HEAVY_FEDERATION_ATTESTATION_P002_v1.json"
d = json.loads(P.read_text(encoding="utf-8"))
assert d["schema"] == "qps.gm_i_a.fast_heavy.federation_attestation.v1"
assert d["pulse_id"] == "GM-I-A-MCLOCK-P002"
assert d["provider_repo"] == "GBOGEB/CoolProp"
assert d["source_head_sha"] == "a88d6e8cc24402868afab39a71fc49fcacec08c8"
assert d["source_merge_sha"] == "e31433c4427be2aaad064294e6c6cab1843537df"
assert d["workflow"]["run_id"] == 36226071145
assert d["workflow"]["conclusion"] == "success"
assert d["heavy"]["conclusion"] == "success"
assert d["heavy"]["queue_seconds"] == 36
assert d["heavy"]["checkout_seconds"] == 34
assert d["heavy"]["build_seconds"] == 211
assert d["heavy"]["artifact"]["wheel_sha256"] == "d342c86635472a63af42d0999e4dc0026dc185cf9e62c35ea0ca64bb02d8a7b4"
assert d["fast"]["conclusion"] == "success"
assert d["fast"]["queue_seconds"] == 35
assert d["fast"]["execute_seconds"] == 7
assert d["fast"]["calculations_passed"] == 2
assert d["fast"]["build_invoked"] is False
assert d["fast"]["source_checkout_performed"] is False
assert d["authority"]["authority_transfer"] is False
assert d["authority"]["engineering_promotion"] == "WITHHELD"
assert d["federation"]["state"] == "READY_FOR_INDEPENDENT_CONSUMER"
print("PASS GM-I-A P002 FAST/HEAVY federation attestation")
