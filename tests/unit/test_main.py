from strava_predictor.__main__ import server_config


def test_server_binds_to_localhost_by_default():
    settings = server_config()
    assert settings["host"] == "127.0.0.1"
    assert settings["port"] == 8000


def test_server_does_not_log_request_bodies():
    settings = server_config()
    assert settings["log_level"] == "warning"
