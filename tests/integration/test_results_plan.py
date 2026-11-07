from tests.integration.helpers import make_client, post


def test_plan_tables(load_fixture):
    html = post(make_client(), load_fixture("typical_runner.csv"), weeks_to_race="12").text
    assert 'id="plan"' in html
    assert html.count('class="week"') == 12
    for heading in ("Day", "Type", "Distance (km)", "Target pace"):
        assert heading in html
    for text in ("Phase", "Base", "Taper", "Easy", "Hard", "Race", "km"):
        assert text in html
    assert "fast end of the easy pace range" in html


def test_stretch_target_note_for_unlikely_goal(load_fixture):
    html = post(make_client(), load_fixture("typical_runner.csv"), goal_pace="3:30").text
    assert "Unlikely in this time" in html
    assert "training targets the stretch pace" in html


def test_hard_total_note_for_one_week_marathon(load_fixture):
    html = post(
        make_client(),
        load_fixture("typical_runner.csv"),
        race_distance_km="42.195",
        weeks_to_race="1",
        days_per_week="2",
    ).text
    assert 'id="hard-total-note"' in html
    assert "outside the 15–20% range" in html
