"""Fail closed on invalid Cedefop schema and non-finite health burden."""
from io import BytesIO
import zipfile
import pytest
from app.ingestion.cedefop_oja_imbalance import detect_schema,parse_csv
from app.ingestion.eea_health_burden import parse_eea_pm25_burden_archive,DATASET_VERSION


def test_cefedop_missing_occupation_label_not_parser_ready(tmp_path):
    headers=["ISCO_4","score"]
    assert detect_schema(headers)["ready_for_parser_implementation"] is False
    path=tmp_path/"oja.csv"
    path.write_text("ISCO_4,score\n2522,0.7\n",encoding="utf-8")
    with pytest.raises(ValueError,match="schema is not recognised"):
        parse_csv(path)


def make_archive(value,unit="NR"):
    output=BytesIO()
    with zipfile.ZipFile(output,"w") as z:
        z.writestr(f"{DATASET_VERSION}.csv",
            "code,dimension,dimension_label,unit,unit_label,geo,geo_label,time,obs_value,obs_status\n"
            f"11_52,PMD,Premature deaths,{unit},Number,ES12,Asturias,2023,{value},\n")
    return output.getvalue()


def test_health_burden_finite_number_preserved():
    rows=parse_eea_pm25_burden_archive(make_archive("812"),country_prefixes={"ES"})
    assert rows[0]["value"]==812.0


@pytest.mark.parametrize("bad",["nan","inf","-inf"])
def test_health_burden_nonfinite_source_rejected(bad):
    with pytest.raises(ValueError,match="nonfinite"):
        parse_eea_pm25_burden_archive(make_archive(bad),country_prefixes={"ES"})


def test_health_burden_wrong_unit_rejected():
    with pytest.raises(ValueError,match="Unexpected EEA health-burden unit"):
        parse_eea_pm25_burden_archive(make_archive("812",unit="PC"),country_prefixes={"ES"})
