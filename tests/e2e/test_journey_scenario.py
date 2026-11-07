"""User Story 3 in a real browser."""

from pathlib import Path

from playwright.sync_api import Page, expect

from tests.e2e.test_journey_check_goal import fill_inputs

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_try_another_scenario(page: Page, base_url: str):
    page.goto(base_url)
    page.set_input_files("#csv_file", str(FIXTURES / "typical_runner.csv"))
    fill_inputs(page, weeks="12")
    page.click("button[type=submit]")
    expect(page.locator("#plan .week")).to_have_count(12)

    page.fill("#weeks_to_race", "20")
    page.click("button[type=submit]")
    expect(page.locator("#results")).to_be_visible()
    expect(page.locator("#plan .week")).to_have_count(20)
