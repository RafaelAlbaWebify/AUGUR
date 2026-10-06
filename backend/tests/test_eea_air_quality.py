from app.ingestion.eea_air_quality import TARGET_COUNTRIES


def test_eea_pm25_target_countries_are_registered_scope():
    assert TARGET_COUNTRIES == {"ES", "PT", "IE"}
