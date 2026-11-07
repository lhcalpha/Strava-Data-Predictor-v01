"""In-memory store of parsed runs, so scenarios can be regenerated without re-uploading (R7).

Only parsed activities are kept, never the CSV text. Nothing is written to disk; entries vanish
after SESSION_TTL_S idle seconds, when evicted, or when the server stops.
"""

import secrets
import threading
from collections import OrderedDict
from collections.abc import Callable

from strava_predictor import config
from strava_predictor.domain.models import Activity

TOKEN_BYTES = 32


class SessionStore:
    def __init__(self, clock: Callable[[], float]):
        self._clock = clock
        self._entries: OrderedDict[str, tuple[float, tuple[Activity, ...]]] = OrderedDict()
        self._lock = threading.Lock()

    def __len__(self) -> int:
        return len(self._entries)

    def _expire(self, now: float) -> None:
        for token in [
            t for t, (seen, _) in self._entries.items() if now - seen > config.SESSION_TTL_S
        ]:
            del self._entries[token]

    def put(self, activities: tuple[Activity, ...], token: str | None = None) -> str:
        with self._lock:
            now = self._clock()
            self._expire(now)
            token = token if token in self._entries else secrets.token_urlsafe(TOKEN_BYTES)
            self._entries[token] = (now, tuple(activities))
            self._entries.move_to_end(token)
            while len(self._entries) > config.MAX_SESSIONS:
                self._entries.popitem(last=False)
            return token

    def get(self, token: str | None) -> tuple[Activity, ...] | None:
        if not token:
            return None
        with self._lock:
            now = self._clock()
            self._expire(now)
            entry = self._entries.get(token)
            if entry is None:
                return None
            self._entries[token] = (now, entry[1])
            self._entries.move_to_end(token)
            return entry[1]
