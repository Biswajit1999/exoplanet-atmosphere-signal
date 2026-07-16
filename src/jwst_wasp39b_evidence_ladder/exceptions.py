class ProjectError(RuntimeError):
    """Base exception for actionable project failures."""


class DataSchemaError(ProjectError):
    """Raised when an input product does not match the documented schema."""


class ProvenanceError(ProjectError):
    """Raised when required provenance metadata are absent or inconsistent."""


class ArchiveAccessError(ProjectError):
    """Raised when a real archive query or download fails or is inaccessible."""


class ConvergenceError(ProjectError):
    """Raised when a numerical fit fails to converge or is ill-conditioned."""


class InsufficientDataError(ProjectError):
    """Raised when there is not enough data to compute a requested statistic."""
