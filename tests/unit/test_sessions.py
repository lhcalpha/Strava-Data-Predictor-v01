from strava_predictor import config
from strava_predictor.web.sessions import SessionStore
from tests.integration.helpers import FakeClock
from tests.unit.domain_helpers import act


def _runs():
    return (act(1, 5.0, 30.0), act(2, 6.0, 36.0))


def test_put_and_get():
    store = SessionStore(FakeClock())
    token = store.put(_runs())
    assert len(token) >= 40
    assert store.get(token) == _runs()


def test_tokens_are_random():
    store = SessionStore(FakeClock())
    assert store.put(_runs()) != store.put(_runs())


def test_unknown_token():
    store = SessionStore(FakeClock())
    assert store.get("nope") is None
    assert store.get(None) is None


def test_expires_after_idle_time():
    clock = FakeClock()
    store = SessionStore(clock)
    token = store.put(_runs())
    clock.now += config.SESSION_TTL_S - 1
    assert store.get(token) is not None
    clock.now += config.SESSION_TTL_S - 1  # refreshed by the previous get
    assert store.get(token) is not None
    clock.now += config.SESSION_TTL_S + 1
    assert store.get(token) is None


def test_oldest_entries_are_evicted():
    clock = FakeClock()
    store = SessionStore(clock)
    tokens = []
    for _ in range(config.MAX_SESSIONS + 2):
        tokens.append(store.put(_runs()))
        clock.now += 1
    assert store.get(tokens[0]) is None
    assert store.get(tokens[1]) is None
    assert store.get(tokens[-1]) is not None
    assert len(store) == config.MAX_SESSIONS


def test_replace_existing_token():
    store = SessionStore(FakeClock())
    token = store.put(_runs())
    store.put((act(3, 9.0, 50.0),), token=token)
    assert len(store.get(token)) == 1


def test_stores_activities_not_text():
    store = SessionStore(FakeClock())
    token = store.put(_runs())
    assert all(not isinstance(item, str | bytes) for item in store.get(token))
