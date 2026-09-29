"""Verify model artifacts and the governance registry remain consistent."""
from __future__ import annotations

import json
from pathlib import Path

from forex_ai.model_validation import validate_all_models

EXPECTED_SYSTEM_STATUS = "GOVERNED / NOT LIVE"
EXPECTED_TRAINED_STATUS = "trained_not_approved_for_live"


def main() -> int:
    registry_path = Path("model_registry.json")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    assert registry.get("system_status") == EXPECTED_SYSTEM_STATUS
    assert registry.get("approval_required") is True

    results = validate_all_models("models")
    registry_models = registry.get("models", {})

    instruments = {result.instrument for result in results}
    registered = set(registry_models)

    assert instruments == registered, (
        f"registry/artifact instrument mismatch: "
        f"artifacts={sorted(instruments)}, registry={sorted(registered)}"
    )

    for result in results:
        entry = registry_models[result.instrument]
        payload = json.loads(
            (Path("models") / entry["model_id"] / "model.json").read_text(
                encoding="utf-8"
            )
        )
        assert entry["model_id"] == payload.get("model_id")
        assert entry["status"] == payload.get("status")
        assert entry["status"] == EXPECTED_TRAINED_STATUS

    print("Model registry consistency verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
