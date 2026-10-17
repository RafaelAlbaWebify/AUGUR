"""Adversarial STAS/CLSSI source-integrity regressions."""
from pathlib import Path
import pytest
from app.ingestion import cedefop_stas as stas
from app.ingestion import cedefop_clssi as clssi


def _sheets(values, *, isco=25, sheet="ameco_2d"):
    return [{"sheet":sheet,"rows":[
        ["scenario","country","country_code","oc","oc_code",2026],
        *[["Aligned_forecast_Ameco","Spain","ES","ICT",isco,value] for value in values],
    ]}]


@pytest.mark.parametrize("value",[float("nan"),float("inf"),float("-inf")])
def test_stas_nonfinite_rejected(monkeypatch,tmp_path,value):
    monkeypatch.setattr(stas,"workbook_preview",lambda path,max_rows=100000:_sheets([value]))
    with pytest.raises(ValueError,match="Invalid STAS source value"):
        stas.parse_stas_workbook(tmp_path/"stas.xlsx")


@pytest.mark.parametrize("isco",[25.5,255,-1])
def test_stas_invalid_isco_rejected(monkeypatch,tmp_path,isco):
    monkeypatch.setattr(stas,"workbook_preview",lambda path,max_rows=100000:_sheets([100],isco=isco))
    with pytest.raises(ValueError,match="Invalid STAS ISCO"):
        stas.parse_stas_workbook(tmp_path/"stas.xlsx")


def test_stas_conflicting_duplicate_rejected(monkeypatch,tmp_path):
    monkeypatch.setattr(stas,"workbook_preview",lambda path,max_rows=100000:_sheets([100,130]))
    with pytest.raises(ValueError,match="Conflicting STAS duplicate"):
        stas.parse_stas_workbook(tmp_path/"stas.xlsx")


def test_stas_identical_duplicate_keeps_one(monkeypatch,tmp_path):
    monkeypatch.setattr(stas,"workbook_preview",lambda path,max_rows=100000:_sheets([100,100]))
    rows=stas.parse_stas_workbook(tmp_path/"stas.xlsx")
    assert len(rows)==1 and rows[0]["employment_level_thousands"]==100


class Response:
    headers={"content-type":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    url="https://example.test/dataset.xlsx"
    content=b"<html>not-xlsx</html>"
    def raise_for_status(self): pass


class Client:
    def get(self,*args,**kwargs): return Response()


def test_stas_html_disguised_as_xlsx_does_not_overwrite_existing(tmp_path):
    path=tmp_path/"stas.xlsx"
    path.write_bytes(b"old")
    with pytest.raises(ValueError,match="invalid ZIP signature"):
        stas.download_workbook(Client(),path,download_url=Response.url)
    assert path.read_bytes()==b"old"


def test_clssi_html_disguised_as_xlsx_does_not_overwrite_existing(tmp_path):
    path=tmp_path/"clssi.xlsx"
    path.write_bytes(b"old")
    with pytest.raises(ValueError,match="invalid ZIP signature"):
        clssi.download_workbook(path,client=Client(),url=Response.url)
    assert path.read_bytes()==b"old"
