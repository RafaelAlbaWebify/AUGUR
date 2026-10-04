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

Role:
- contextual occupation vacancy-rate evidence where available.

Limitations:
- experimental;
- online-ad / portal and occupational coverage bias;
- not equivalent to a personal probability of finding work.

## Planned verified sources

### Cedefop — Real-time occupational shortage based on OJAs

Dataset:
- version: 2026-05;
- licence: CC BY 4.0;
- DOI: 10.2906/752555516245105;
- canonical page: https://www.cedefop.europa.eu/en/datasets/oja-imbalance-occupations
- published direct file name: `cedefop-oja-imbalance-2026-05.csv`.

Methodological role:
- exploratory EU27 occupation-level recruitment-difficulty / shortage signal;
- combines OJA labour-demand growth, digital-skill demand change, ad duration,
  non-native-language share and OJA-to-employment change;
- published score is normalised 0–1.

AUGUR role:
- occupation-level demand/shortage context only;
- must be labelled exploratory;
- must not be used as skill-level demand share or employer count;
- must preserve Cedefop's representativeness/classification warning.

Integration status:
- source identified;
- not active until the CSV bytes and schema are inspected and pinned in the ingestion pipeline.

### Cedefop — STAS

Dataset:
- Short-term anticipation of skills trends and VET demand;
- updated twice per year;
- licence: CC BY 4.0;
- DOI: 10.2906/467749508762302;
- canonical page: https://www.cedefop.europa.eu/en/datasets/stas
- published Jan-2026 file name: `stas_dataset_release_jan_2026.xlsx`;
- a newer August 2026 release is listed by Cedefop and should be preferred once its file is inspected.

Methodological role:
- short-term employment projections by occupation;
- uses EU LFS employment, European Job Vacancy Statistics and AMECO alignment.

AUGUR role:
- short-term occupation outlook;
- separate from OJA shortage;
- never displayed as skill-level demand.

Integration status:
- source identified;
- not active until the latest downloadable workbook is inspected and version-pinned.

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
