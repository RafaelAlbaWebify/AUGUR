# AUGUR labour-market demand sources

## Purpose

This document defines which external labour-market evidence AUGUR may use for the Skills & Languages and CareerFit layers.

AUGUR must distinguish:

1. occupation taxonomy and skill relationships;
2. observed labour-market imbalance / recruitment difficulty;
3. short-term occupation employment outlook;
4. detailed online-job-ad skill demand;
5. personal skill/language recommendations.

No source may be promoted to a more granular role than its published methodology supports.

## Active evidence

### ESCO

Role:
- occupation taxonomy;
- essential/optional skill relationships;
- multilingual occupation/skill labels;
- ISCO mapping.

ESCO is **not** employer-demand frequency and must never be presented as "X% of employers want skill Y".

### EURES / ELA

Role:
- shortage/surplus context;
- country and occupation-group labour-market evidence.

Limitations:
- incomplete occupational coverage;
- methodology and granularity vary;
- shortage classification does not imply a specific salary or personal hiring probability.

### Eurostat experimental vacancy evidence

Dataset:
- code: `jvs_a_isco3_r1`;
- frequency: annual;
- granularity: ISCO 3-digit occupation and country/NUTS 1 where available;
- active AUGUR country coverage: Spain and Portugal;
- Ireland: source coverage unavailable in the published experimental dataset.

Role:
- contextual occupation vacancy-rate evidence where available;
- CareerFit prefers ISCO-3 evidence for the resolved occupation before any broader fallback;
- vacancy-rate evidence remains context-only and does not override EURES/ELA shortage/surplus gates.

Methodology:
- Eurostat combines official JVS totals with EU-LFS occupied-post estimates and Online Job Advertisement shares to disaggregate vacancy rates by occupation and region;
- the resulting occupation/region breakdown is published as experimental statistics.

Limitations:
- experimental;
- online-ad / portal and occupational coverage bias;
- occupations commonly advertised online, including many IT roles, can be overrepresented relative to public-sector or offline recruitment;
- geographic coverage is incomplete and must be surfaced as source coverage, not treated as zero demand;
- not equivalent to a personal probability of finding work.

## Active forward-looking occupation evidence

### Cedefop Skills Forecast 2026

Dataset:
- projections to 2035;
- sector, occupation and education;
- licence: CC BY 4.0;
- DOI: 10.2906/087829408840877.

Access:
- full spreadsheet is supplied through Cedefop's dataset request form.

AUGUR role:
- medium-term occupation/sector outlook once reproducible access is available.

### Cedefop Skills-OVATE

Role:
- detailed OJA-based skill and occupation demand;
- country/region views;
- ESCO/O*NET skill classification;
- occupation focus and skill-share analysis.

Current access constraint:
- public interactive visualisation is Tableau-based;
- detailed data access is not currently treated as a stable public REST ingestion source.

AUGUR rule:
- do not scrape Tableau;
- do not infer job-posting shares from ESCO;
- integrate Skills-OVATE only when a reproducible downloadable/API/microdata workflow is available.

## Product implications

Until detailed OJA skill-demand data is integrated, Skills & Languages may truthfully show:

- occupation match;
- ESCO matched/missing skills;
- EURES/ELA shortage/surplus;
- Eurostat vacancy context;
- Cedefop occupation shortage/outlook once integrated;
- user-declared language and CEFR evidence.

It must withhold:

- skill demand percentage;
- skill YoY growth;
- number/diversity of employers;
- salary premium by skill;
- language demand share in job ads;
- "rising skill" rankings.

Those fields should remain explicitly unavailable rather than synthesized from taxonomy data.


## Explicit access-gated evidence

### Skills-OVATE detailed skill-demand trends

Status:
- source access gated.

Reason:
- Cedefop exposes interactive Skills-OVATE dashboards and quarterly updates;
- access to detailed data is organised through Eurostat's Microdata access portal;
- AUGUR does not treat Tableau visualisations as a stable ingestion API and does not scrape them.

AUGUR behaviour:
- CareerFit exposes `skill_demand_trend_evidence.status = source_access_gated`;
- ESCO occupation-skill relationships remain taxonomy evidence only;
- no skill demand share, YoY growth or employer frequency is inferred.

### Skills-OVATE language requirements in OJAs

Status:
- source access gated.

Reason:
- detailed OJA language analytics require the same microdata-access route;
- the public 2026 Cedefop OJA imbalance CSV exposes one combined EU27 occupation score;
- its non-native-language component is not separately published in a form AUGUR can reproducibly ingest.

AUGUR behaviour:
- CareerFit exposes `language_oja_requirements_evidence.status = source_access_gated`;
- zero or null is never interpreted as zero employer demand;
- declared CEFR and target-country language evidence remain separate from OJA demand.

## Active future shortage evidence

### Cedefop CLSSI

Dataset:
- official 2026 Cedefop Labour and Skills Shortage Index workbook;
- country-specific sheets;
- ISCO-08 2-digit occupation groups;
- forecast horizon: 2035;
- active AUGUR coverage: Spain, Portugal and Ireland.

Methodology:
- the published Labour Shortage Index is on a 1–4 scale;
- 1 indicates no shortage / surplus conditions and 4 indicates intense shortage;
- the overall index is the simple average of three published 1–4 components:
  - employment growth;
  - replacement demand;
  - supply-demand imbalance.

AUGUR behaviour:
- the official workbook is downloaded reproducibly from Cedefop;
- country is read from the workbook sheet name;
- occupation labels are mapped to ISCO-2 only through an explicit canonical/verified alias table;
- unknown labels, duplicate country/ISCO rows, invalid 1–4 scores, component-code mismatches or overall-index arithmetic mismatches fail the import;
- CareerFit exposes CLSSI as `future_shortage_index_evidence`;
- CLSSI remains context-only and does not change EURES market gates, CareerFit completeness or TTV timing;
- missing CLSSI evidence is never interpreted as zero shortage pressure.

Validated live import:
- 114 rows;
- countries: ESP, IRL, PRT;
- horizon: 2035;
- release: 2026.

## Active occupation trend evidence

### Cedefop STAS

Role:
- short-term occupation employment outlook;
- country-specific;
- ISCO 2-digit preferred, ISCO 1-digit fallback;
- 2026–2027 horizons in the currently integrated release.

AUGUR behaviour:
- CareerFit exposes a structured occupation trend derived from published STAS growth values;
- direction is sign-based only (`positive_growth`, `negative_growth`, or `zero_growth`);
- this is explicitly employment outlook, not OJA demand growth, statistical significance or a personal hiring probability.


## ELA Annex extraction workflow

The 2025 ELA shortage/surplus Annex is published as a PDF rather than a stable CSV/API.

AUGUR now supports:

```powershell
.\build-eures-market-evidence-from-annex.ps1
```

The workflow downloads the official Annex, extracts the ruled table with `pdfplumber`, writes a normalized occupation/country table and passes it through the existing full-ESCO resolver.

The extractor is intentionally review-oriented:

- no OCR is used;
- conflicting duplicate occupation rows block readiness;
- ambiguous ESCO matches remain unresolved;
- duplicate ISCO assignments remain unresolved;
- production EURES evidence is never rewritten automatically.

This removes manual PDF-to-CSV normalization while preserving the human-review boundary for semantic occupation mapping.

STAS acquisition boundary:
- the August 2026 spreadsheet is an official downloadable Cedefop dataset and the parser/importer are fully implemented;
- Cedefop currently returns HTTP 403 to AUGUR's automated dataset-page resolver, so AUGUR does not guess a release URL or silently fall back to January 2026;
- when the current XLSX is already local, import remains reproducible and schema-validated;
- STAS is therefore the remaining manual acquisition exception in the current Cedefop evidence stack.
