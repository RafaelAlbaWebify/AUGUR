"""B02 safety: readiness and numeric evidence must be consistent."""
import io
import zipfile
import pytest
from app.ingestion.cedefop_oja_imbalance import detect_schema, parse_csv
from app.ingestion.eea_health_burden import parse_eea_pm25_burden_archive, DATASET_VERSION


def archive(value, unit="NR"):
    data=io.BytesIO()
    with zipfile.ZipFile(data,"w") as z:
        z.writestr(f"{DATASET_VERSION}.csv",
            "code,dimension,dimension_label,unit,unit_label,geo,geo_label,time,obs_value,obs_status\n"
            f"11_52,PMD,Deaths,{unit},Number,ES12,Asturias,2023,{value},\n")
    return data.getvalue()


def test_cedefop_missing_label_not_accepted_or_parsed(tmp_path):
    assert detect_schema(["ISCO_4","score"])["ready_for_parser_implementation"] is False
    path=tmp_path/"incomplete.csv"
    path.write_text("ISCO_4,score\n2522,0.5\n")
    with pytest.raises(ValueError,match="schema is not recognised"):
        parse_csv(path)


@pytest.mark.parametrize("value",["nan","inf","-1"])
def test_eea_invalid_numeric_rejected(value):
    with pytest.raises(ValueError,match="Invalid EEA health burden value"):
        parse_eea_pm25_burden_archive(archive(value))


def test_eea_wrong_unit_rejected():
    with pytest.raises(ValueError,match="Unexpected EEA health burden unit"):
        parse_eea_pm25_burden_archive(archive("25","PC"))


def test_eea_valid_count_preserved():
    rows=parse_eea_pm25_burden_archive(archive("25"))
    assert len(rows)==1 and rows[0]["value"]==25 and rows[0]["unit_code"]=="NR"
