"""Every rule value used by the app, named and traced to its source.

FR-### refers to specs/001-race-pace-training-plan/spec.md; R## refers to research.md in the same
folder. Domain code must take numbers from here (Constitution II).
"""

# --- Units -------------------------------------------------------------------------------
METRES_PER_KM = 1000
METRES_PER_MILE = 1609.344
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
DAYS_PER_WEEK = 7
PERCENT = 100
FLOAT_TOLERANCE = 1e-9  # guards floor() and boundary comparisons against float error
RELATIVE_TOLERANCE = 1e-6  # float error allowed when comparing sums of many distances

# --- Reading the CSV (FR-009 to FR-016, R2 to R5) ------------------------------------------
WINDOW_WEEKS = 12  # FR-009
STALE_DATA_DAYS = 14  # FR-016
MIN_USABLE_RUNS = 3  # FR-015
HR_VALID_MIN = 30  # FR-012
HR_VALID_MAX = 250  # FR-012
AVG_HR_PATTERN = r"\bavg\s*:?\s*(\d{2,3})\b"  # FR-012, R5
RUN_ACTIVITY_TYPES = frozenset({"Run", "Trail Run", "Virtual Run"})  # R4
PACE_PLAUSIBLE_MIN = 120  # FR-014: faster than 2:00 per km is not a usable distance
PACE_PLAUSIBLE_MAX = 1200  # FR-014: slower than 20:00 per km is not a usable distance
MILES_RATIO_TOLERANCE = 0.05  # R2: share of difference allowed when matching the km/mile ratio
DATE_FORMATS = (  # R3
    "%b %d, %Y, %I:%M:%S %p",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d",
)
REQUIRED_COLUMNS = (  # FR-010
    "Activity Date",
    "Activity Name",
    "Activity Type",
    "Activity Description",
    "Distance",
    "Moving Time",
)

# --- Classifying effort (FR-017, FR-018) ---------------------------------------------------
EASY_HR_FRACTION = 0.75
HARD_HR_FRACTION = 0.82
INTERVAL_KEYWORDS = ("interval", "repeat")

# --- Predicting pace (FR-019 to FR-025) ----------------------------------------------------
RIEGEL_EXPONENT = 1.06  # FR-019
MIN_PREDICTION_RUN_KM = 3.0  # FR-019
TOP_PREDICTIONS = 3  # FR-019
TEN_K_KM = 10.0  # FR-036: easy pace comes from today's 10 km estimate
WEEKLY_RATE_SAFE = 0.002  # FR-022
WEEKLY_RATE_LIKELY = 0.003  # FR-022
WEEKLY_RATE_STRETCH = 0.005  # FR-022
IMPROVEMENT_CAP_SAFE = 0.04  # FR-022 (clarified 2026-11-05)
IMPROVEMENT_CAP_LIKELY = 0.06  # FR-022 (clarified 2026-11-05)
IMPROVEMENT_CAP_STRETCH = 0.10  # FR-022 (clarified 2026-11-05)
LOW_VOLUME_MULTIPLIER = 1.25  # FR-023
MIN_ACTIVE_WEEKS = 8  # FR-023
LOW_VOLUME_KM = 15.0  # FR-023
HIGH_VOLUME_MULTIPLIER = 0.75  # FR-023
HIGH_VOLUME_KM = 60.0  # FR-023
LONG_RUN_TARGETS = ((5.0, 8.0), (10.0, 12.0), (21.0975, 18.0), (42.195, 30.0))  # FR-024
LONG_RUN_MIN_KM = 8.0  # FR-024
LONG_RUN_MAX_KM = 35.0  # FR-024
LONG_RUN_GROWTH = 0.10  # FR-025 and R15
SHORTFALL_STEP = 0.10  # FR-025
SLOWDOWN_PER_STEP = 0.01  # FR-025

# --- Rating the goal (FR-026, FR-027) ------------------------------------------------------
VERY_AMBITIOUS_MARGIN = 0.02
MIN_HARD_RUNS_FOR_CONFIDENCE = 3
MIN_HR_SHARE = 0.5

# --- Generating the plan (FR-028 to FR-037, R13 to R16) ------------------------------------
TAPER_WEEKS_BY_DISTANCE = ((10.0, 1), (21.1, 2))  # FR-029: (up to km, weeks)
TAPER_WEEKS_LONG_RACE = 3  # FR-029
TAPER_CUTS = {1: (0.40,), 2: (0.25, 0.50), 3: (0.20, 0.35, 0.55)}  # FR-029 (clarified)
PHASE_SHARE_BASE = 0.4  # FR-030
PHASE_SHARE_BUILD = 0.4  # FR-030
PHASE_SHARE_PEAK = 0.2  # FR-030
START_VOLUME_WEEKS = 4  # FR-031
MAX_WEEKLY_INCREASE = 0.10  # FR-032
LIGHTER_WEEK_EVERY = 4  # FR-032
LIGHTER_WEEK_CUT_MIN = 0.20  # FR-032
LIGHTER_WEEK_CUT_MAX = 0.25  # FR-032
LIGHTER_WEEK_CUT = 0.225  # R14: middle of the FR-032 range
VOLUME_GROWTH_RATE = 0.08  # R14
PEAK_VOLUME_MULTIPLIER = 1.5  # R14
MAX_WEEKLY_HARD_SHARE = 0.20  # FR-035
PLAN_HARD_SHARE_MIN = 0.15  # FR-035
PLAN_HARD_SHARE_MAX = 0.20  # FR-035
HARD_SHARE_BY_PHASE = {"BASE": 0.15, "BUILD": 0.18, "PEAK": 0.19, "TAPER": 0.15}  # R16
EASY_PACE_FACTOR_MIN = 1.18  # FR-036
EASY_PACE_FACTOR_MAX = 1.27  # FR-036
WARMUP_KM = 2.0  # R15
COOLDOWN_KM = 1.5  # R15
LONG_RUN_MAX_SHARE = 0.5  # R15
FEW_DAYS_PER_WEEK = 3  # R15: at or below this, one hard session a week
HARD_SESSIONS_FEW_DAYS = 1  # R15
HARD_SESSIONS_BY_PHASE = {"BASE": 1, "BUILD": 2, "PEAK": 2, "TAPER": 1}  # R15
HARD_SHARE_SEARCH_STEPS = 40  # R16: bisection steps when long races push the plan total over 20%

# --- Inputs (FR-002 to FR-006) -------------------------------------------------------------
RACE_KM_MAX = 100.0
RACE_KM_WARN_MIN = 3.0
RACE_KM_WARN_MAX = 42.195
WEEKS_MIN = 1
WEEKS_MAX = 52
WEEKS_WARN_MIN = 4
GOAL_PACE_MIN_S = 120  # spec Assumptions: 2:00 per km
GOAL_PACE_MAX_S = 900  # spec Assumptions: 15:00 per km
DAYS_MIN = 2
DAYS_MAX = 7
MAX_HR_DEFAULT = 201
MAX_HR_MIN = 100
MAX_HR_MAX = 240

# --- Web (R6 to R9) -----------------------------------------------------------------------
SESSION_TTL_S = 7200  # R7
MAX_SESSIONS = 10  # R7
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # plan: reject uploads above 10 MB
REQUEST_OVERHEAD_BYTES = 1024 * 1024  # room for form fields; larger bodies are refused unread
HOST = "127.0.0.1"  # plan: bind to localhost only
PORT = 8000
