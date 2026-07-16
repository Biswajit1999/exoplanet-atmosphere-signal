"""Writer/validator for results/summary.json, matching results/summary.schema.json."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jwst_wasp39b_evidence_ladder.exceptions import DataSchemaError

_REQUIRED_TOP_KEYS = ("project", "data_kind", "metrics", "provenance", "warnings")
_REQUIRED_METRIC_KEYS = ("name", "estimate", "units", "sample_size")


@dataclass(frozen=True)
class Metric:
    name: str
    estimate: float
    units: str
    sample_size: int
    uncertainty_low: float | None = None
    uncertainty_high: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "estimate": self.estimate,
            "uncertainty_low": self.uncertainty_low,
            "uncertainty_high": self.uncertainty_high,
            "units": self.units,
            "sample_size": self.sample_size,
        }


def validate_summary(payload: dict[str, Any]) -> None:
    missing = [key for key in _REQUIRED_TOP_KEYS if key not in payload]
    if missing:
        raise DataSchemaError(f"summary payload missing required keys: {missing}")
    if not isinstance(payload["metrics"], list):
        raise DataSchemaError("summary 'metrics' must be a list")
    for i, metric in enumerate(payload["metrics"]):
        missing_metric = [key for key in _REQUIRED_METRIC_KEYS if key not in metric]
        if missing_metric:
            raise DataSchemaError(f"metrics[{i}] missing required keys: {missing_metric}")
    if not isinstance(payload["warnings"], list):
        raise DataSchemaError("summary 'warnings' must be a list")
    if not isinstance(payload["provenance"], dict):
        raise DataSchemaError("summary 'provenance' must be an object")


def write_summary(
    path: str | Path,
    project: str,
    data_kind: str,
    metrics: list[Metric],
    provenance: dict[str, Any],
    warnings: list[str],
) -> dict[str, Any]:
    payload = {
        "project": project,
        "data_kind": data_kind,
        "metrics": [m.to_dict() for m in metrics],
        "provenance": provenance,
        "warnings": warnings,
    }
    validate_summary(payload)
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
