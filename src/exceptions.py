"""Domain errors. Fail loud — never silently continue on invalid pipeline state."""


class ExperimentError(Exception):
    """Base for all experiment-pipeline errors."""


class EmptyCohortError(ExperimentError):
    """Cohort filter returned zero rows."""


class MissingColumnError(ExperimentError):
    """A required column is absent from an input table."""


class ImbalanceError(ExperimentError):
    """Variant sizes differ beyond the configured tolerance."""
