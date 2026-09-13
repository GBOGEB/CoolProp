#!/usr/bin/env python3
"""Mission I control probe.

Binds the derived CoolProp mission status to the latest successful W145 runtime
and emits queue/step timing telemetry from GitHub Actions.  The probe is
stdlib-only so the control lane does not depend on the package it supervises.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API_ROOT = "https://api.github.com"
DEFAULT_WORKFLOW = "qps_w145_lkt_2kop_crosswalk.yml"
DEFAULT_HOOK = Path("qps/recon/TEMPORAL_STATUS_HOOK.yaml")
DEFAULT_REPORT = Path("qps/recon/STATUS_REPORT.md")
DEFAULT_OUTPUT = Path("qps/recon/receipts/mission_i_phase_telemetry.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "GBOGEB/CoolProp"))
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW)
    parser.add_argument("--hook", type=Path, default=DEFAULT_HOOK)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def api_json(url: str) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "qps-mission-i-control",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def iso_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def duration_s(start: str | None, end: str | None) -> float | None:
    if not start or not end:
        return None
    return max(0.0, (iso_dt(end) - iso_dt(start)).total_seconds())


def latest_successful_run(repo: str, workflow: str) -> dict[str, Any]:
    encoded_workflow = urllib.parse.quote(workflow, safe="")
    url = f"{API_ROOT}/repos/{repo}/actions/workflows/{encoded_workflow}/runs?status=success&per_page=20"
    payload = api_json(url)
    runs = [run for run in payload.get("workflow_runs", []) if run.get("conclusion") == "success"]
    if not runs:
        raise RuntimeError(f"no successful runs found for {workflow}")
    return runs[0]


def fetch_job(run: dict[str, Any]) -> dict[str, Any]:
    payload = api_json(run["jobs_url"])
    jobs = payload.get("jobs", [])
    if not jobs:
        raise RuntimeError(f"run {run['id']} has no jobs")
    for job in jobs:
        if job.get("name") == "lkt-2kop-crosswalk":
            return job
    return jobs[0]


def parse_control_binding(hook_text: str) -> dict[str, Any]:
    match = re.search(r"(?ms)^latest_qualified_runtime:\n(?P<block>(?:^  .*\n?)+)", hook_text)
    if not match:
        raise RuntimeError("TEMPORAL_STATUS_HOOK.yaml has no root latest_qualified_runtime block")
    block = match.group("block")

    def field(name: str) -> str:
        item = re.search(rf"(?m)^  {re.escape(name)}:\s*['\"]?([^'\"\n]+)['\"]?\s*$", block)
        if not item:
            raise RuntimeError(f"latest_qualified_runtime.{name} is missing")
        return item.group(1).strip()

    return {
        "workflow_file": field("workflow_file"),
        "run_id": int(field("run_id")),
        "source_sha": field("source_sha"),
        "receipt_sha256": field("receipt_sha256"),
        "status": field("status"),
    }


def step_durations(job: dict[str, Any]) -> dict[str, float]:
    durations: dict[str, float] = {}
    for step in job.get("steps", []):
        value = duration_s(step.get("started_at"), step.get("completed_at"))
        if value is not None:
            durations[step.get("name", f"step-{step.get('number')}")] = value
    return durations


def build_telemetry(repo: str, workflow: str, run: dict[str, Any], job: dict[str, Any], binding: dict[str, Any], report_text: str) -> dict[str, Any]:
    steps = step_durations(job)
    phases = {
        "checkout_s": steps.get("Checkout exact source head", 0.0),
        "setup_python_s": steps.get("Run actions/setup-python@v5", 0.0),
        "prerequisites_s": steps.get("Install build prerequisites", 0.0),
        "build_install_s": steps.get("Build and install exact CoolProp checkout", 0.0),
        "probe_s": steps.get("Execute exact-source W145 crosswalk", 0.0),
        "checksum_s": steps.get("Bind receipt checksum", 0.0),
        "artifact_upload_s": steps.get("Upload exact-run receipt", 0.0),
    }
    measured_total = sum(phases.values())
    dominant_name, dominant_seconds = max(phases.items(), key=lambda item: item[1])
    dominant_share = (dominant_seconds / measured_total) if measured_total else 0.0

    latest_sha = run["head_sha"]
    latest_run_id = int(run["id"])
    mismatches: list[str] = []
    if binding["workflow_file"] != workflow:
        mismatches.append("workflow_file")
    if binding["source_sha"] != latest_sha:
        mismatches.append("source_sha")
    if binding["run_id"] != latest_run_id:
        mismatches.append("run_id")
    if binding["status"] != "PASS":
        mismatches.append("status")
    if latest_sha not in report_text:
        mismatches.append("status_report_source_sha")
    if str(latest_run_id) not in report_text:
        mismatches.append("status_report_run_id")

    guard_status = "PASS" if not mismatches else "RED"
    first_red = None if not mismatches else f"STATUS_STALE_RUNTIME_EVIDENCE:{mismatches[0]}"

    queue = duration_s(run.get("created_at"), job.get("started_at"))
    execute = duration_s(job.get("started_at"), job.get("completed_at"))

    return {
        "schema": "qps.mission_i.phase_telemetry.v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "workflow": {
            "file": workflow,
            "workflow_id": run.get("workflow_id"),
            "run_id": latest_run_id,
            "run_number": run.get("run_number"),
            "event": run.get("event"),
            "head_sha": latest_sha,
            "head_branch": run.get("head_branch"),
            "conclusion": run.get("conclusion"),
            "created_at": run.get("created_at"),
            "updated_at": run.get("updated_at"),
            "job_id": job.get("id"),
            "runner_id": job.get("runner_id"),
        },
        "control_binding": binding,
        "guard": {
            "status": guard_status,
            "first_red": first_red,
            "mismatches": mismatches,
        },
        "runtime": {
            "timestamp_resolution_s": 1,
            "queue_s": queue,
            "execute_s": execute,
            "phases": phases,
            "measured_phase_total_s": measured_total,
            "dominant_phase": {
                "name": dominant_name,
                "seconds": dominant_seconds,
                "share_of_measured": round(dominant_share, 6),
            },
        },
        "classification": {
            "runtime_class": "HEAVY_PRODUCER" if phases["build_install_s"] >= 60 else "FAST_CONSUMER_CANDIDATE",
            "fast_probe_candidate": phases["build_install_s"] > max(phases["probe_s"], 1.0) * 10,
            "pc1_candidate": dominant_name,
            "rule": "measure first; optimize build/setup separately from numerical execution",
        },
    }


def main() -> int:
    args = parse_args()
    hook_text = args.hook.read_text(encoding="utf-8")
    report_text = args.report.read_text(encoding="utf-8")
    binding = parse_control_binding(hook_text)
    run = latest_successful_run(args.repo, args.workflow)
    job = fetch_job(run)
    telemetry = build_telemetry(args.repo, args.workflow, run, job, binding, report_text)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(telemetry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(telemetry, indent=2, sort_keys=True))

    if telemetry["guard"]["status"] != "PASS":
        print(f"FIRST_RED={telemetry['guard']['first_red']}", file=sys.stderr)
        return 2
    print("Mission I control PASS: derived status is bound to latest qualified W145 runtime evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
