"""User Story 4 in a real browser."""

from pathlib import Path

from playwright.sync_api import Page, expect

from tests.e2e.test_journey_check_goal import fill_inputs

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_understand_the_data(page: Page, base_url: str):
    page.goto(base_url)
    page.set_input_files("#csv_file", str(FIXTURES / "mixed_quality.csv"))
    fill_inputs(page)
    page.click("button[type=submit]")
    summary = page.locator("#data-summary")
    expect(summary).to_contain_text("Runs used")
    expect(summary).to_contain_text("Not a run")
    expect(summary).to_contain_text("Outside the 12 weeks")
    expect(page.locator("#confidence")).to_contain_text("Low")
