# AUGUR Live Job-Postings Provider Evaluation — 2026-10-07

Status: **provider-neutral contract implemented / no provider configured**

AUGUR's public-data model is operational without a commercial live-postings provider. Live postings are therefore an optional enrichment layer and must not become a hidden dependency for Country Radar, CareerFit completeness or TTV.

## 1. Required AUGUR contract

A provider must support, at minimum:

- active job postings;
- country filtering;
- occupation filtering;
- posting date / bounded observation window.

Preferred additional capabilities:

- regional filtering;
- structured skills;
- language requirements;
- salary context;
- employer;
- historical postings / trend analysis.

Live-postings evidence remains context-only until its provider-specific coverage, deduplication, classification and extraction methodology are documented.

Missing provider access must be represented as `provider_not_configured`, never as zero demand.

## 2. Lightcast

Official documentation:

- https://docs.lightcast.io/lightcast-api/reference/overview-global-job-postings
- https://docs.lightcast.io/lightcast-api/reference/global_postings_post_postings

Observed fit:

- global job-postings dataset;
- filters and enriched fields include occupation, skills and geography;
- suitable for labour-market analytics;
- OAuth 2.0 access with account permissions;
- commercial access required for expanded postings scopes.

Assessment:

**Best semantic fit for AUGUR**, especially for skills/language-demand analytics, but not suitable as an implicit dependency because access is commercial and account-scoped.

## 3. Coresignal

Official documentation / product pages:

- https://coresignal.com/solutions/jobs-data-api/
- https://coresignal.com/pricing/

Observed fit:

- structured global job postings;
- role, company, location and skills filtering;
- active and historical postings;
- developer-facing self-service;
- free trial currently advertised;
- paid plans currently advertised from USD 49/month.

Assessment:

**Best current self-service pilot candidate** if AUGUR needs to demonstrate the value of live postings before committing to a larger commercial source.

A trial may be used only to validate the provider adapter and evidence value. Trial data must not silently become a permanent production dependency.

## 4. Adzuna

Official documentation:

- https://developer.adzuna.com/
- https://developer.adzuna.com/overview
- https://developer.adzuna.com/activedocs

Observed fit:

- current job-ad search;
- country and location search;
- salary, employer and historical salary endpoints;
- developer API keys available;
- Adzuna separately advertises Labour Market Intelligence with historical data, standardised titles and skills.

Assessment:

Useful for **posting-count, salary and basic live-market context**, but the standard public developer API should not be assumed to provide the structured skill/language analytics AUGUR ultimately wants.

## 5. Jooble

Official documentation:

- https://help.jooble.org/en/support/solutions/articles/60001448238-rest-api-documentation

Observed fit:

- REST job-listing API;
- separate API key per country domain;
- free plan documented as 500 lifetime requests per key.

Assessment:

Not suitable as AUGUR's primary analytical provider because the lifetime quota and per-country key model are poor fits for repeatable multi-country evidence refresh.

## 6. Decision

AUGUR will **not configure a live-postings provider yet**.

Implementation order:

1. keep the vendor-neutral `live-postings-v1` contract;
2. expose `provider_not_configured` explicitly in CareerFit and operability;
3. keep live postings non-blocking for the verified public-data model;
4. when a pilot is justified, prefer a short Coresignal self-service evaluation unless Lightcast access is already available;
5. compare the pilot against AUGUR's existing EURES / Eurostat / Cedefop signals;
6. only retain a paid provider if it materially improves decisions through reproducible occupation-, skill-, language- or regional-demand evidence.

A provider must not be adopted merely because it returns more rows.

## 7. Evidence boundary

Live postings may eventually provide:

- active posting counts;
- employer-demand skill shares;
- language-requirement shares;
- posting trends;
- salary context;
- employer concentration.

They must not be converted directly into:

- individual job-finding probability;
- TTV timing;
- an unconditional country ranking;
- zero-demand conclusions when provider coverage is absent.

ESCO remains taxonomy evidence, not employer-demand frequency.
