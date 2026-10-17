"""Read-only inspection of IMF's officially published October 2026 WEO workbook."""
import io
import json
import httpx
from openpyxl import load_workbook
from app.ingestion.imf_weo_official import normalize_official_weo
from scripts.verify_weo_disposable_readthrough import verify_weo_roundtrip

URL="https://data.imf.org/-/media/iData/External-Storage/Documents/0FA3DC49A04D446E9D69DBEB29979E1C/en/WEOOct2026all.xlsx"


def inspect_workbook(payload: bytes) -> dict:
    if not payload.startswith(b"PK"):
        raise ValueError("IMF download is not an XLSX archive")
    book=load_workbook(io.BytesIO(payload),read_only=True,data_only=True)
    try:
        sheets=[]
        for sheet in book.worksheets:
            samples=[]
            for row in sheet.iter_rows(min_row=1,max_row=min(12,sheet.max_row),max_col=min(18,sheet.max_column),values_only=True):
                samples.append([str(value)[:90] if value is not None else None for value in row])
            sheets.append({"name":sheet.title,"max_rows":sheet.max_row,"max_columns":sheet.max_column,
                           "sample":samples})
        countries=book["Countries"]
        header=[str(v) if v is not None else "" for v in next(countries.iter_rows(min_row=1,max_row=1,values_only=True))]
        representative=[]
        for record in countries.iter_rows(min_row=2,values_only=True):
            if (record[2] in {"ESP","IRL","PRT","USA"} and
                record[4] in {"NGDP_RPCH","PCPIPCH","LUR"}):
                representative.append({
                    "country":record[2],"indicator":record[4],
                    "latest_actual_annual_data":record[15],
                    "unit":record[9],
                    "values":{header[i]:record[i] for i in range(18,min(81,len(header))) if header[i] in {"2023","2024","2025","2026","2027"}},
                })
        return {"status":"read_only_source_inspection","format":"xlsx","sheets":sheets,
                "country_sheet_headers":header,"representative":representative}
    finally:
        book.close()


def main():
    with httpx.Client(timeout=120,follow_redirects=True) as client:
        r=client.get(URL,headers={"Accept":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","User-Agent":"AUGUR-OfficialDataProbe/1.0"})
        print("IMF official workbook HTTP:",r.status_code,"size:",len(r.content))
        r.raise_for_status()
        result=inspect_workbook(r.content)
        rows, contract=normalize_official_weo(r.content,{"ESP","PRT","IRL","USA"})
        result["official_contract"]=contract
        result["official_contract"]["parsed_rows"]=len(rows)
        result["disposable_db_acceptance"]=verify_weo_roundtrip(rows)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
