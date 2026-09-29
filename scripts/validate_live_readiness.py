"""Run the model live-readiness gate in CI."""
from pathlib import Path
import sys

from forex_ai.model_validation import validate_all_models, write_report


def main() -> int:
    results = validate_all_models()
    write_report(results, "validation/live_readiness_report.json")
    for result in results:
        state = "PASS" if result.passed else "BLOCKED"
        print(f"{state} {result.instrument}: {', '.join(result.reasons) or 'all gates passed'}")
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
