"""Immutable value objects for the domain (see data-model.md). Nothing here is stored on disk.

Times are seconds, distances km, and paces seconds per km unless a name says otherwise.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class ExclusionReason(StrEnum):
    NOT_A_RUN = "NOT_A_RUN"
    OUTSIDE_WINDOW = "OUTSIDE_WINDOW"
    NO_DISTANCE = "NO_DISTANCE"
    NO_MOVING_TIME = "NO_MOVING_TIME"
    IMPLAUSIBLE_PACE = "IMPLAUSIBLE_PACE"


class EffortClass(StrEnum):
    EASY = "EASY"
    MODERATE = "MODERATE"
    HARD = "HARD"
    UNKNOWN = "UNKNOWN"


class DataErrorCode(StrEnum):
    MISSING_COLUMNS = "MISSING_COLUMNS"
    EMPTY_FILE = "EMPTY_FILE"
    MALFORMED_CSV = "MALFORMED_CSV"
    TOO_FEW_RUNS = "TOO_FEW_RUNS"
    NO_RUN_OVER_3KM = "NO_RUN_OVER_3KM"


class DataError(Exception):
    """The data cannot support a prediction; the message is shown to the runner."""

    def __init__(self, code: DataErrorCode, message: str, details: tuple[str, ...] = ()):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


class Projection(StrEnum):
    SAFE = "SAFE"
    LIKELY = "LIKELY"
    STRETCH = "STRETCH"


class Rating(StrEnum):
    CONSERVATIVE = "CONSERVATIVE"
    REALISTIC = "REALISTIC"
    AMBITIOUS = "AMBITIOUS"
    VERY_AMBITIOUS = "VERY_AMBITIOUS"
    UNLIKELY = "UNLIKELY"


class Confidence(StrEnum):
    NORMAL = "NORMAL"
    LOW = "LOW"


class Phase(StrEnum):
    BASE = "BASE"
    BUILD = "BUILD"
    PEAK = "PEAK"
    TAPER = "TAPER"


class SessionKind(StrEnum):
    EASY = "EASY"
    LONG = "LONG"
    HARD = "HARD"
    RACE = "RACE"


@dataclass(frozen=True)
class Activity:
    date: date
    name: str
    activity_type: str
    description: str
    distance_km: float | None
    moving_time_s: float | None
    avg_hr: int | None
    is_interval: bool
    exclusion: ExclusionReason | None = None

    @property
    def pace_s_per_km(self) -> float | None:
        if not self.distance_km or not self.moving_time_s:
            return None
        return self.moving_time_s / self.distance_km


@dataclass(frozen=True)
class RunnerInputs:
    race_distance_km: float
    weeks_to_race: int
    goal_pace_s_per_km: int
    days_per_week: int
    max_hr: int


@dataclass(frozen=True)
class DataWarning:
    code: str
    message: str


@dataclass(frozen=True)
class DataSummary:
    runs_used: int
    excluded: dict[ExclusionReason, int]
    runs_with_hr: int
    hard_runs_used: int
    date_range: tuple[date, date] | None
    weeks_with_runs: int
    avg_weekly_km_12: float
    avg_weekly_km_4: float
    longest_run_km: float
    warnings: tuple[DataWarning, ...] = ()

    @property
    def excluded_total(self) -> int:
        return sum(self.excluded.values())


@dataclass(frozen=True)
class ProjectedResult:
    time_s: float
    pace_s_per_km: float


@dataclass(frozen=True)
class Prediction:
    race_distance_km: float
    today_time_s: float
    basis_runs: tuple[Activity, ...]
    hard_runs_used: int
    used_fallback: bool
    interval_only: bool
    rate_multiplier: float
    caps_applied: frozenset[Projection]
    long_run_target_km: float
    reachable_long_run_km: float
    distance_slowdown_pct: int
    safe: ProjectedResult
    likely: ProjectedResult
    stretch: ProjectedResult
    today_10k_pace_s_per_km: float

    @property
    def today_pace_s_per_km(self) -> float:
        return self.today_time_s / self.race_distance_km


@dataclass(frozen=True)
class GoalRating:
    rating: Rating
    confidence: Confidence
    confidence_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class Session:
    day: int
    kind: SessionKind
    distance_km: float
    pace_s_per_km: float  # hard, race, or the fast end of the easy range
    hard_km: float = 0.0
    warmup_km: float = 0.0
    cooldown_km: float = 0.0


@dataclass(frozen=True)
class PlanWeek:
    number: int
    phase: Phase
    is_lighter: bool
    is_race_week: bool
    training_km: float
    total_km: float
    total_time_s: float
    hard_time_s: float
    hard_pace_s_per_km: float
    long_run_km: float
    sessions: tuple[Session, ...]

    @property
    def hard_share(self) -> float:
        return self.hard_time_s / self.total_time_s if self.total_time_s else 0.0

    @property
    def easy_share(self) -> float:
        return 1.0 - self.hard_share


@dataclass(frozen=True)
class TrainingPlan:
    target_pace_s_per_km: float
    targets_stretch: bool
    stretch_pace_s_per_km: float
    today_10k_pace_s_per_km: float
    easy_pace_range: tuple[float, float]
    start_km: float
    weeks: tuple[PlanWeek, ...]
    total_hard_share: float
    notes: tuple[str, ...] = ()
    hard_total_note: str | None = None  # set when the total is outside 15-20% (FR-035)


@dataclass(frozen=True)
class AnalysisResult:
    summary: DataSummary
    prediction: Prediction
    rating: GoalRating
    plan: TrainingPlan | None = None
    activities: tuple[Activity, ...] = field(default=(), repr=False)
