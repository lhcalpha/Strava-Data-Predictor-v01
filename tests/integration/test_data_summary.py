import re

from tests.integration.helpers import make_client, post


def _section(html: str) -> str:
    match = re.search(r'<section class="card" id="data-summary">(.*?)</section>', html, re.S)
    assert match, "data summary section missing"
    return re.sub(r"\s+", " ", match.group(1))


def _row(section: str, label: str) -> str:
    match = re.search(rf"<th[^>]*>{re.escape(label)}</th>\s*<td[^>]*>(.*?)</td>", section)
    assert match, label
    return match.group(1).strip()


def test_mixed_quality_counts(load_fixture):
    html = post(make_client(), load_fixture("mixed_quality.csv")).text
    section = _section(html)
    assert _row(section, "Runs used") == "12"
    assert _row(section, "Runs excluded") == "8"
    assert _row(section, "Runs with usable heart rate") == "5 of 12"
    assert _row(section, "Hard runs used") == "3"
    assert _row(section, "Date range") == "2026-09-21 to 2026-11-04"
    for reason, count in (
        ("Not a run", 2),
        ("Outside the 12 weeks", 3),
        ("No usable distance", 1),
        ("No moving time", 1),
        ("Pace faster than 2:00 or slower than 20:00 per km", 1),
    ):
        assert re.search(rf"{re.escape(reason)}[^<]*</td>\s*<td[^>]*>{count}</td>", section), reason


def test_mixed_quality_confidence(load_fixture):
    html = post(make_client(), load_fixture("mixed_quality.csv")).text
    confidence = re.search(r'id="confidence">(.*?)</div>', html, re.S).group(1)
    assert "Low" in confidence
    assert "5 of 12 runs have a usable heart rate" in confidence


def test_effort_thresholds_are_shown(load_fixture):
    html = post(make_client(), load_fixture("typical_runner.csv")).text
    section = _section(html)
    assert "151" in section and "165" in section


def test_stale_data_warning(load_fixture):
    html = post(make_client(), load_fixture("stale.csv")).text
    assert "may be out of date" in _section(html)


def test_no_exclusions(load_fixture):
    section = _section(post(make_client(), load_fixture("typical_runner.csv")).text)
    assert _row(section, "Runs excluded") == "0"
