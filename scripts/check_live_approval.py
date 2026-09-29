"""Final auditable approval gate for one model/instrument pair."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from forex_ai.model_validation import (
    validate_approval_record,
    validate_model_artifact,
    validate_paper_evidence,
)
from forex_ai.risk_validation import validate_trade_risk


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--paper", required=True)
    parser.add_argument("--approval", required=True)
    parser.add_argument("--risk-json", required=True)
    args = parser.parse_args()

    model = validate_model_artifact(args.model)
    if not model.instrument:
        print("APPROVAL BLOCKED: model instrument is missing.")
        return 1

    model_payload = json.loads(Path(args.model).read_text(encoding="utf-8"))
    model_id = str(model_payload.get("model_id") or model_payload.get("instrument", ""))
    paper = validate_paper_evidence(
        args.paper,
        expected_model_id=model_id,
        expected_instrument=model.instrument,
    )
    approval = validate_approval_record(
        args.approval,
        expected_model_id=model_id,
        expected_instrument=model.instrument,
    )

    try:
        risk_payload = json.loads(Path(args.risk_json).read_text(encoding="utf-8"))
        risk = validate_trade_risk(**risk_payload)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        risk = False

    gates = {
        "model_validation": model.passed,
        "paper_evidence": paper,
        "approval_record": approval,
        "risk_controls": risk,
    }
    print(json.dumps(gates, indent=2))
    if not all(gates.values()):
        print("APPROVAL BLOCKED")
        return 1

    print("APPROVAL GATES PASSED — human authorization record is present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
