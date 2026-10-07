from __future__ import annotations

from app.ingestion.eures_annex_pdf import normalize_annex_table


def test_normalize_annex_table_handles_multiline_cells_and_country_lists():
    table = [
        [
            "Occupation",
            "Countries reporting a shortage",
            "Countries reporting a surplus",
        ],
        [
            "Administrative and executive\nsecretaries",
            "BE, NL, RO",
            "AT, BE, BG, CZ, DE, EE, ES, FI, LT, LV, NO, PT, SI",
        ],
        [
            "Agricultural and industrial machinery\nmechanics and repairers",
            "AT, BE, BG, CZ, DE, DK, EE, FR, IT, LT, LU, NL, NO, PT, SE, SI",
            "FI, LV, RO",
        ],
    ]

    rows = normalize_annex_table(table)

    assert rows == [
        {
            "occupation_label": "Administrative and executive secretaries",
            "shortage_countries": "BE NL RO",
            "surplus_countries": "AT BE BG CZ DE EE ES FI LT LV NO PT SI",
        },
        {
            "occupation_label": "Agricultural and industrial machinery mechanics and repairers",
            "shortage_countries": "AT BE BG CZ DE DK EE FR IT LT LU NL NO PT SE SI",
            "surplus_countries": "FI LV RO",
        },
    ]


def test_normalize_annex_table_ignores_non_table_rows():
    table = [
        ["Table 21: Transnational matching possibilities, 2025", None, None],
        [
            "Occupation",
            "Countries reporting a shortage",
            "Countries reporting a surplus",
        ],
        ["EURES | footer", None, None],
        ["Applications programmers", "AT, BE, BG, CY, HR, HU, NL, RO, SE, SI", "CZ, DE, EL, FI, LV"],
        ["Page 4", None, None],
    ]

    rows = normalize_annex_table(table)

    assert rows == [
        {
            "occupation_label": "Applications programmers",
            "shortage_countries": "AT BE BG CY HR HU NL RO SE SI",
            "surplus_countries": "CZ DE EL FI LV",
        }
    ]


def test_normalize_annex_table_requires_expected_headers():
    assert normalize_annex_table([
        ["Occupation", "Shortage", "Surplus"],
        ["Systems analysts", "IE", "PT"],
    ]) == []
