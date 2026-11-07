"""User Story 2 in a real browser."""

from pathlib import Path

from playwright.sync_api import Page, expect

from tests.e2e.test_journey_check_goal import fill_inputs

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_get_a_training_plan(page: Page, base_url: str):
    page.goto(base_url)
    page.set_input_files("#csv_file", str(FIXTURES / "typical_runner.csv"))
    fill_inputs(page, weeks="10")
    page.click("button[type=submit]")
    weeks = page.locator("#plan .week")
    expect(weeks).to_have_count(10)
    last_row = weeks.last.locator("tbody tr").last
    expect(last_row).to_contain_text("Race")
