"""Error journey: a bad file shows a clear error, and a good file then works with kept values."""

from pathlib import Path

from playwright.sync_api import Page, expect

from tests.e2e.test_journey_check_goal import fill_inputs

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_error_then_recover(page: Page, base_url: str):
    page.goto(base_url)
    page.set_input_files("#csv_file", str(FIXTURES / "missing_columns.csv"))
    fill_inputs(page, distance="21.1")
    page.click("button[type=submit]")
    expect(page.locator("#data-error")).to_contain_text("Moving Time")
    expect(page.locator("#plan")).to_have_count(0)
    expect(page.locator("#race_distance_km")).to_have_value("21.1")

    page.set_input_files("#csv_file", str(FIXTURES / "typical_runner.csv"))
    page.click("button[type=submit]")
    expect(page.locator("#results")).to_be_visible()
    expect(page.locator("#summary")).to_contain_text("21.1 km race")


def test_field_error_is_shown_beside_the_field(page: Page, base_url: str):
    page.goto(base_url)
    page.set_input_files("#csv_file", str(FIXTURES / "typical_runner.csv"))
    fill_inputs(page, weeks="60")
    page.click("button[type=submit]")
    expect(page.locator("#weeks_to_race-error")).to_be_visible()
    expect(page.locator("#goal_pace")).to_have_value("4:50")
