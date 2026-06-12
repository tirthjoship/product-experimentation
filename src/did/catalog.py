"""Phase A event catalog — written from public record ONLY, before any data access.

Each entry pre-registers hypothesis, primary outcome, expected sign, and donut
assignment (treated bloc / control bloc / excluded middle) per spec §4 + §6.
Selection among viable candidates is mechanical: feasibility (Phase B) checks
pre-period cell counts only, never outcomes.
"""

from dataclasses import dataclass

from src.exceptions import UnknownEventError

# Brazilian UFs by IBGE macro-region (public record).
NORTH = ("AC", "AM", "AP", "PA", "RO", "RR", "TO")
NORTHEAST = ("AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE")
CENTER_WEST = ("DF", "GO", "MS", "MT")
SOUTHEAST = ("ES", "MG", "RJ", "SP")
SOUTH = ("PR", "RS", "SC")
ALL_UFS = frozenset(NORTH + NORTHEAST + CENTER_WEST + SOUTHEAST + SOUTH)


@dataclass(frozen=True)
class EventDefinition:
    name: str
    description: str
    source: str  # public-record citation (gate condition 1)
    boundary_date: str  # ISO date; post period starts here (inclusive)
    estimation_start: str
    estimation_end_exclusive: str
    outcome: str  # "delivery_days" | "log_orders"
    expected_sign: int  # +1 / -1
    treated_states: tuple[str, ...]
    control_states: tuple[str, ...]
    excluded_states: tuple[str, ...]
    viable_on_paper: bool
    rationale: str


CATALOG: tuple[EventDefinition, ...] = (
    EventDefinition(
        name="truckers_strike_2018",
        description=(
            "Nationwide truckers' strike (greve dos caminhoneiros), 2018-05-21 to "
            "2018-05-30: road freight halted; long-haul routes to North/Northeast "
            "depend on trucking from Southeast distribution hubs."
        ),
        source=(
            "Widely documented national event; e.g. "
            "https://en.wikipedia.org/wiki/2018_Brazil_truck_drivers%27_strike"
        ),
        boundary_date="2018-05-21",
        estimation_start="2018-01-01",
        estimation_end_exclusive="2018-09-01",
        outcome="delivery_days",
        expected_sign=1,  # deliveries slower, more so far from hubs
        treated_states=NORTH + NORTHEAST,
        control_states=SOUTHEAST + SOUTH,
        excluded_states=CENTER_WEST,
        viable_on_paper=True,
        rationale=(
            "Externally dated; exposure gradient is geographic (freight distance "
            "from SE hubs); donut drops ambiguous Center-West."
        ),
    ),
    EventDefinition(
        name="black_friday_2017",
        description="Black Friday demand spike, 2017-11-24.",
        source="Annual retail calendar date (public record).",
        boundary_date="2017-11-24",
        estimation_start="2017-08-01",
        estimation_end_exclusive="2018-01-01",
        outcome="log_orders",
        expected_sign=1,
        treated_states=NORTH + NORTHEAST,
        control_states=SOUTHEAST + SOUTH,
        excluded_states=CENTER_WEST,
        viable_on_paper=False,
        rationale=(
            "NOT viable on paper: exposure is national — no geography-only "
            "treated/control contrast exists (gate condition 2 unsatisfiable). "
            "Kept in catalog to document the rejection."
        ),
    ),
    EventDefinition(
        name="carnival_2018",
        description="Carnival week, 2018-02-13 (Shrove Tuesday).",
        source="Brazilian national calendar (public record).",
        boundary_date="2018-02-13",
        estimation_start="2017-11-01",
        estimation_end_exclusive="2018-04-01",
        outcome="log_orders",
        expected_sign=-1,
        treated_states=("RJ", "BA", "PE", "SP"),  # major public celebrations
        control_states=SOUTH + ("MG", "ES"),
        excluded_states=NORTH
        + ("AL", "CE", "MA", "PB", "PI", "RN", "SE")
        + CENTER_WEST,
        viable_on_paper=False,
        rationale=(
            "NOT viable on paper: ~1-week transient shock with ambiguous sign and "
            "too few post-boundary weeks of differential exposure for ≥3 lead/lag "
            "structure. Kept to document the rejection."
        ),
    ),
)


def viable_candidates() -> tuple[EventDefinition, ...]:
    return tuple(e for e in CATALOG if e.viable_on_paper)


def get_event(name: str) -> EventDefinition:
    for e in CATALOG:
        if e.name == name:
            return e
    raise UnknownEventError(f"event not in catalog: {name!r}")
