#!/usr/bin/env python3
import json
from pathlib import Path

P = Path(__file__).resolve().parent / "federation" / "GM_I_A_FAST_HEAVY_FEDERATION_ATTESTATION_v1.json"
d = json.loads(P.read_text(encoding="utf-8"))
assert d["schema"] == "qps.gm_i_a.fast_heavy.federation_attestation.v1"
assert d["provider_repo"] == "GBOGEB/CoolProp"
assert d["workflow"]["conclusion"] == "success"
assert d["heavy"]["conclusion"] == "success"
assert d["fast"]["conclusion"] == "success"
assert d["fast"]["calculations_passed"] > 0
assert d["fast"]["build_invoked"] is False
assert d["fast"]["source_checkout_performed"] is False
assert d["heavy"]["artifact"]["digest"].startswith("sha256:")
assert d["fast"]["artifact"]["digest"].startswith("sha256:")
assert d["authority"]["authority_transfer"] is False
assert d["authority"]["engineering_promotion"] == "WITHHELD"
assert d["federation"]["state"] == "READY_FOR_INDEPENDENT_CONSUMER"
print("PASS GM-I-A FAST/HEAVY federation attestation")
