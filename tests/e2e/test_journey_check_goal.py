"""User Story 1 in a real browser."""

import time
from pathlib import Path

from playwright.sync_api import Page, expect

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SC_001_LIMIT_S = 120


def fill_inputs(page: Page, distance="10", weeks="12", goal="4:50", days="4") -> None:
    page.fill("#race_distance_km", distance)
    page.fill("#weeks_to_race", weeks)
    page.fill("#goal_pace", goal)
    page.fill("#days_per_week", days)


def test_check_a_race_goal(page: Page, base_url: str):
    started = time.monotonic()
    page.goto(base_url)
    page.set_input_files("#csv_file", str(FIXTURES / "typical_runner.csv"))
    fill_inputs(page)
    page.click("button[type=submit]")
    expect(page.locator("#results")).to_be_visible()
    expect(page.locator("#summary")).to_contain_text("Today")
    expect(page.locator("#summary")).to_contain_text("Stretch")
    expect(page.locator("#rating")).to_contain_text("Conservative")
    expect(page.locator("#confidence")).to_be_visible()
    assert time.monotonic() - started < SC_001_LIMIT_S
