"""Domain errors. Fail loud — never silently continue on invalid pipeline state."""


class ExperimentError(Exception):
    """Base for all experiment-pipeline errors."""


class EmptyCohortError(ExperimentError):
    """Cohort filter returned zero rows."""


class MissingColumnError(ExperimentError):
    """A required column is absent from an input table."""


class ImbalanceError(ExperimentError):
    """Variant sizes differ beyond the configured tolerance."""


class UnknownEventError(ExperimentError):
    """Requested event name is not in the Plan 4 catalog."""


class BlindingError(ExperimentError):
    """Post-period data requested without a committed GO gate verdict."""
