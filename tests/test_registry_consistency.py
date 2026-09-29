from pathlib import Path
import json

from scripts.verify_model_registry import main


def test_registry_matches_all_model_artifacts():
    assert main() == 0


def test_registry_contains_only_governed_model_status():
    payload = json.loads(Path("model_registry.json").read_text(encoding="utf-8"))
    assert payload["system_status"] == "GOVERNED / NOT LIVE"
    assert all(
        item["status"] == "trained_not_approved_for_live"
        for item in payload["models"].values()
    )
