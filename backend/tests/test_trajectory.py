from app.services.trajectory import DEFAULT_HORIZONS


def test_default_horizons_are_expected():
    assert DEFAULT_HORIZONS == [2030, 2035, 2045]
