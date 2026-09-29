"""Generate an auditable, non-promotional live-readiness report."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

# Make direct script execution resolve imports from the repository root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from forex_ai.model_validation import validate_all_models


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default="models")
    parser.add_argument("--output", default="validation/live_readiness_report.json")
    args = parser.parse_args()

    results = validate_all_models(args.model_dir, as_of=date.today())
    payload = {
        "report_type": "forex_live_readiness",
        "generated_at": date.today().isoformat(),
        "system_status": "GOVERNED / NOT LIVE",
        "approval_policy": "evidence_and_human_approval_required",
        "models": [
            {
                "instrument": r.instrument,
                "passed": r.passed,
                "checks": r.checks,
                "blocking_reasons": list(r.reasons),
            }
            for r in results
        ],
        "all_model_validation_gates_passed": all(r.passed for r in results),
        "note": (
            "This report does not grant approval. Human approval, paper evidence, "
            "risk controls, and independent validation remain mandatory."
        ),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
