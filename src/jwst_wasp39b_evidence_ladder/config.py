"""Typed configuration model for config/analysis.yml."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from jwst_wasp39b_evidence_ladder.exceptions import DataSchemaError


@dataclass(frozen=True)
class ProjectMeta:
    title: str
    repository: str
    author: str
    curation_status: str
    priority: float


@dataclass(frozen=True)
class ExecutionConfig:
    seed: int
    output_directory: str
    overwrite: bool
    fail_on_warning: bool


@dataclass(frozen=True)
class InputConfig:
    data_mode: str
    manifest: str
    raw_directory: str
    example_directory: str


@dataclass(frozen=True)
class ValidationConfig:
    minimum_sample_size: int
    bootstrap_resamples: int
    confidence_level: float


@dataclass(frozen=True)
class ProvenanceConfig:
    record_environment: bool
    record_git_commit: bool
    verify_checksums: bool


@dataclass(frozen=True)
class AnalysisConfig:
    project: ProjectMeta
    execution: ExecutionConfig
    input: InputConfig
    validation: ValidationConfig
    provenance: ProvenanceConfig


def _require(mapping: dict[str, Any], key: str, section: str) -> Any:
    if key not in mapping:
        raise DataSchemaError(f"config section '{section}' is missing required key '{key}'")
    return mapping[key]


def _require_section(raw: dict[str, Any], section: str) -> dict[str, Any]:
    value = raw.get(section)
    if not isinstance(value, dict):
        raise DataSchemaError(f"config is missing required section '{section}'")
    return value


def load_config(path: str | Path) -> AnalysisConfig:
    config_path = Path(path)
    if not config_path.is_file():
        raise DataSchemaError(f"config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if not isinstance(raw, dict):
        raise DataSchemaError(f"config file is not a mapping: {config_path}")

    project_raw = _require_section(raw, "project")
    execution_raw = _require_section(raw, "execution")
    input_raw = _require_section(raw, "input")
    validation_raw = _require_section(raw, "validation")
    provenance_raw = _require_section(raw, "provenance")

    project = ProjectMeta(
        title=_require(project_raw, "title", "project"),
        repository=_require(project_raw, "repository", "project"),
        author=_require(project_raw, "author", "project"),
        curation_status=_require(project_raw, "curation_status", "project"),
        priority=float(_require(project_raw, "priority", "project")),
    )
    execution = ExecutionConfig(
        seed=int(_require(execution_raw, "seed", "execution")),
        output_directory=_require(execution_raw, "output_directory", "execution"),
        overwrite=bool(_require(execution_raw, "overwrite", "execution")),
        fail_on_warning=bool(_require(execution_raw, "fail_on_warning", "execution")),
    )
    input_cfg = InputConfig(
        data_mode=_require(input_raw, "data_mode", "input"),
        manifest=_require(input_raw, "manifest", "input"),
        raw_directory=_require(input_raw, "raw_directory", "input"),
        example_directory=_require(input_raw, "example_directory", "input"),
    )
    validation = ValidationConfig(
        minimum_sample_size=int(_require(validation_raw, "minimum_sample_size", "validation")),
        bootstrap_resamples=int(_require(validation_raw, "bootstrap_resamples", "validation")),
        confidence_level=float(_require(validation_raw, "confidence_level", "validation")),
    )
    if not (0.0 < validation.confidence_level < 1.0):
        raise DataSchemaError("validation.confidence_level must be in (0, 1)")

    provenance = ProvenanceConfig(
        record_environment=bool(_require(provenance_raw, "record_environment", "provenance")),
        record_git_commit=bool(_require(provenance_raw, "record_git_commit", "provenance")),
        verify_checksums=bool(_require(provenance_raw, "verify_checksums", "provenance")),
    )

    return AnalysisConfig(
        project=project,
        execution=execution,
        input=input_cfg,
        validation=validation,
        provenance=provenance,
    )
