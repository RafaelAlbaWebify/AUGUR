import { expect, test, type Page } from '@playwright/test'

const countries = [
  { iso2: 'ES', iso3: 'ESP', name: 'Spain', region: 'Europe', subregion: 'Southern Europe', currency: 'EUR', eu_member: true, eurozone_member: true, oecd_member: true },
  { iso2: 'PT', iso3: 'PRT', name: 'Portugal', region: 'Europe', subregion: 'Southern Europe', currency: 'EUR', eu_member: true, eurozone_member: true, oecd_member: true },
  { iso2: 'IE', iso3: 'IRL', name: 'Ireland', region: 'Europe', subregion: 'Northern Europe', currency: 'EUR', eu_member: true, eurozone_member: true, oecd_member: true },
]

function metric(country: string) {
  const value = country === 'ESP' ? 10.4 : country === 'PRT' ? 6.4 : 4.5
  return {
    country_iso3: country,
    indicator_id: 'unemployment_rate',
    name: 'Unemployment, total (% of total labor force)',
    dimension: 'productive_capacity',
    period: 2025,
    value,
    unit: 'percent',
    source_id: 'EUROSTAT',
  }
}

async function mockApi(page: Page) {
  await page.route('http://127.0.0.1:8020/api/**', async route => {
    const url = new URL(route.request().url())
    const path = url.pathname
    const country = path.match(/\/countries\/(ESP|PRT|IRL)\//)?.[1] ?? 'ESP'
    let body: unknown

    if (path.endsWith('/career-fit')) {
      body = {
        target_country_iso3: country,
        status: 'profession_missing',
        occupation: {
          status: 'profession_missing',
          occupation_group: null,
          matched_terms: [],
        },
        market_signal: null,
        vacancy_demand_evidence: {
          status: 'available',
          isco_major: 'OC3',
          vacancy_rate_pct: 3.4,
          period: '2026-Q2',
          nace_scope: 'B-T',
          source_id: 'EUROSTAT',
          dataset_id: 'jvs_q_isco_r21',
          granularity: 'isco_major_group',
          role: 'context_only',
        },
        skill_match: {
          status: 'not_evaluated',
          matched_skills: [],
          missing_skills: [],
        },
        evidence_complete: false,
        rule_version: 'EURES_COUNTRY_LMI_2024',
        source: {
          label: country === 'ESP'
            ? 'EURES Labour Market Information: Spain'
            : country === 'PRT'
            ? 'EURES Labour Market Information: Portugal'
            : 'EURES Labour Market Information: Ireland',
          url: 'https://eures.europa.eu/',
          evidence_id: 'eures_country_lmi_2024_conditions',
          rule_version: 'EURES_COUNTRY_LMI_2024',
          report_year: 2025,
          conditions_year: 2024,
          report_url: 'https://eures.europa.eu/',
          scope: 'broad_occupation_group',
        },
        notes: [],
      }
    } else if (path.endsWith('/language-fit')) {
      body = {
        target_country_iso3: country,
        status: 'target_language_missing',
        target_languages: [country === 'ESP' ? 'Spanish' : country === 'PRT' ? 'Portuguese' : 'English'],
        matches: [{
          language: country === 'ESP' ? 'Spanish' : country === 'PRT' ? 'Portuguese' : 'English',
          declared_cefr: null,
          meets_work_ready_heuristic: false,
        }],
        work_ready_threshold: 'B2',
        work_ready: false,
        method: 'labour_market_language_heuristic_v1',
        notes: [],
      }
    } else if (path.endsWith('/ttv')) {
      body = {
        target_country_iso3: country,
        method: 'ttv_dependency_graph_v1',
        stage_order: ['legal_fit', 'language_fit', 'career_fit', 'financial_fit'],
        stages: {
          legal_fit: { ready: false, status: 'insufficient_profile', evidence_state: 'implemented' },
          language_fit: { ready: false, status: 'target_language_missing', evidence_state: 'implemented' },
          career_fit: { ready: false, status: 'profession_missing', evidence_state: 'partial' },
          financial_fit: { ready: false, status: 'insufficient_profile', evidence_state: 'partial' },
        },
        blocked_by: ['legal_fit', 'language_fit', 'career_fit', 'financial_fit'],
        blocker_details: [
          { stage_id: 'legal_fit', status: 'insufficient_profile', evidence_state: 'implemented' },
          { stage_id: 'language_fit', status: 'target_language_missing', evidence_state: 'implemented' },
          { stage_id: 'career_fit', status: 'profession_missing', evidence_state: 'partial' },
          { stage_id: 'financial_fit', status: 'insufficient_profile', evidence_state: 'partial' },
        ],
        dependency_ready: false,
        temporal_evidence_state: 'not_implemented',
        temporal_model_version: null,
        temporal_evidence_ready: false,
        temporal_evidence: {
          engine_version: 'ttv-temporal-evidence-v1',
          calendar_ready: false,
          unavailable_stages: ['language', 'skills', 'financial', 'employment'],
          candidate_range: null,
          stages: {
            legal: { status: 'unavailable', weeks_min: null, weeks_max: null, reason: 'legal_timing_not_verified_for_profile' },
            language: {
              status: 'guided_hours_available_calendar_missing',
              weeks_min: null,
              weeks_max: null,
              reason: 'language_study_hours_per_week_missing',
              guided_hours_min: 100,
              guided_hours_max: 250,
              weekly_study_hours: null,
            },
            skills: { status: 'unavailable', weeks_min: null, weeks_max: null, reason: 'career_skill_evidence_incomplete' },
            financial: { status: 'unavailable', weeks_min: null, weeks_max: null, reason: 'financial_transition_duration_not_modelled_for_current_status' },
            employment: { status: 'unavailable', weeks_min: null, weeks_max: null, reason: 'local_job_search_temporal_baseline_not_yet_integrated' },
          },
        },
        candidate_time_range: null,
        estimate_status: 'dependencies_blocked',
        ready_for_time_estimate: false,
        time_estimate: null,
        notes: [],
      }
    } else if (path.endsWith('/legal-fit')) {
      body = {
        target_country_iso3: country,
        status: 'insufficient_profile',
        framework: null,
        work_permit_required: null,
        short_stay: null,
        long_stay: null,
        rule_version: '2026-10-01',
        notes: [],
      }
    } else if (path.endsWith('/financial-fit')) {
      body = {
        target_country_iso3: country,
        status: 'insufficient_profile',
        reason: 'monthly_net_income_missing',
        evidence_state: 'partial',
        evidence_complete: false,
        blockers: ['monthly_net_income'],
        local_income_reference: null,
        national_net_earnings_reference: null,
        portable_income_analysis: null,
        notes: [],
      }
    } else if (path === '/api/profile/readiness') {
      body = {
        profile_id: 'default',
        ready_module_count: 0,
        module_count: 4,
        notes: [],
        modules: {
          legal_fit: { label: 'LegalFit', ready: false, completed_fields: 0, required_fields: 2, missing_fields: ['current_country', 'citizenships'] },
          career_fit: { label: 'CareerFit', ready: false, completed_fields: 0, required_fields: 2, missing_fields: ['profession', 'skills'] },
          language_fit: { label: 'LanguageFit', ready: false, completed_fields: 0, required_fields: 1, missing_fields: ['languages'] },
          financial_fit: { label: 'FinancialFit', ready: false, completed_fields: 0, required_fields: 2, missing_fields: ['current_country', 'monthly_net_income'] },
        },
      }
    } else if (path === '/api/profile') {
      if (route.request().method() === 'PUT') {
        const payload = route.request().postDataJSON()
        body = {
          profile_id: 'default',
          updated_at: '2026-10-01T00:00:00+00:00',
          ...payload,
        }
      } else {
        body = {
          profile_id: 'default',
          age: null,
          current_country: null,
          citizenships: [],
          profession: null,
          skills: [],
          languages: [],
          household_size: 1,
          monthly_net_income: null,
          liquid_savings: null,
          remote_work: false,
          preferences: {},
          updated_at: null,
        }
      }
    } else if (path === '/api/health') {
      body = { status: 'ok', phase: 1, version: 'test', datastores: { sqlite: true, duckdb: true } }
    } else if (path === '/api/operability') {
      body = {
        status: 'partial',
        ready: false,
        analysis_ready: true,
        ttv_temporal_model_ready: false,
        blockers: ['ttv_temporal_model'],
      }
    } else if (path === '/api/countries') {
      body = { countries }
    } else if (path === '/api/compare') {
      const requested = (url.searchParams.get('countries') ?? 'IRL,ESP,PRT').split(',')
      body = {
        countries: requested.map((iso3) => {
          const country = countries.find((item) => item.iso3 === iso3)!
          return { iso3: country.iso3, name: country.name }
        }),
        indicator_count: 1,
        method: 'aligned_current_observations_v1',
        notes: [],
        indicators: [{
          indicator_id: 'unemployment_rate',
          name: 'Unemployment',
          dimension: 'productive_capacity',
          unit: 'percent',
          countries: {
            ESP: { period: 2025, value: 10.4, source_id: 'EUROSTAT' },
            PRT: { period: 2025, value: 6.4, source_id: 'EUROSTAT' },
            IRL: { period: 2025, value: 4.5, source_id: 'EUROSTAT' },
          },
        }],
      }
    } else if (path.endsWith('/snapshot')) {
      body = { country_iso3: country, observation_count: 1, indicators: [metric(country)] }
    } else if (path.endsWith('/trends')) {
      body = { country_iso3: country, indicator_count: 1, indicators: [{ ...metric(country), interpretation_policy: 'lower', target_min: null, target_max: null, trend: { direction: 'decrease', interpretation: 'improving', confidence: 'high', slope_per_year: -0.2, pct_change_1y: -2, pct_change_3y: -5, pct_change_5y: -8, years_used: 6, target_status: null } }] }
    } else if (path.endsWith('/assessment')) {
      body = { country_iso3: country, method: 'test', dimensions: { productive_capacity: { trajectory: 'improving', confidence: 'high', indicator_count: 1, directional_indicator_count: 1, coverage: 1, improving_signals: [{ indicator_id: 'unemployment_rate', name: 'Unemployment', direction: 'decrease', confidence: 'high', pct_change_5y: -8 }], deteriorating_signals: [], stable_signals: [], contextual_signals: [] } } }
    } else if (path.endsWith('/source-quality')) {
      body = { country_iso3: country, indicators: [{ indicator_id: 'unemployment_rate', name: 'Unemployment', dimension: 'productive_capacity', unit: 'percent', source_count: 2, preferred_source_id: 'EUROSTAT', preferred_source_name: 'Eurostat', preferred_period: 2025, preferred_value: metric(country).value, freshest_period: 2025, period_spread: 0, common_period: 2025, common_period_source_count: 2, disagreement_pct: 0.5 }] }
    } else if (path.endsWith('/trajectory')) {
      body = { country_iso3: country, method: 'test', notes: [], horizons: [2030, 2035, 2045].map(year => ({ year, indicator_count: 0, sources: [], indicators: [] })) }
    } else if (path.endsWith('/scenarios')) {
      body = { country_iso3: country, method: 'test', horizons: [2030, 2035, 2045], scenario_names: ['baseline', 'improvement', 'stress'], indicators: [], notes: [] }
    } else {
      body = {}
    }

    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
  })
}

test.beforeEach(async ({ page }) => {
  await mockApi(page)
  await page.goto('/')
})

test('topbar distinguishes evidence readiness from full product status', async ({ page }) => {
  await expect(page.getByText('P1 · ok')).toBeVisible()
  await expect(page.getByText('Evidence · ready')).toBeVisible()
  await expect(page.getByText('Evidence · ready')).toHaveAttribute(
    'title',
    'Product: partial · Blockers: ttv_temporal_model',
  )
})


test('refreshes evidence status when the window regains focus', async ({ page }) => {
  await expect(page.getByText('Evidence · ready')).toBeVisible()

  await page.route(
    'http://127.0.0.1:8020/api/operability',
    async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'partial',
          ready: false,
          analysis_ready: false,
          ttv_temporal_model_ready: false,
          blockers: ['data_sync_stale'],
        }),
      })
    },
  )

  await page.evaluate(() => window.dispatchEvent(new Event('focus')))

  await expect(page.getByText('Evidence · partial')).toBeVisible()
  await expect(page.getByText('Evidence · partial')).toHaveAttribute(
    'title',
    'Product: partial · Blockers: data_sync_stale',
  )
})


test('top navigation uses real routes and unmounts the previous view', async ({ page }) => {
  await expect(page).toHaveURL(/\/country\/ESP\/overview$/)
  await expect(page.getByTestId('world-map')).toBeVisible()

  await page.getByRole('button', { name: 'Outlook' }).click()
  await expect(page).toHaveURL(/\/country\/ESP\/outlook$/)
  await expect(page.getByText('OFFICIAL OUTLOOK')).toBeVisible()
  await expect(page.getByText('AUGUR SCENARIOS')).toBeVisible()
  await expect(page.getByTestId('world-map')).toHaveCount(0)

  await page.getByRole('button', { name: 'Compare' }).click()
  await expect(page).toHaveURL(/\/compare\?countries=IRL%2CESP%2CPRT|\/compare\?countries=IRL,ESP,PRT/)
  await expect(page.getByText('Country comparison')).toBeVisible()
  await expect(page.getByText('OFFICIAL OUTLOOK')).toHaveCount(0)

  await page.getByRole('button', { name: 'Profile' }).click()
  await expect(page).toHaveURL(/\/country\/ESP\/profile$/)
  await expect(page.getByRole('region', { name: 'Personal profile' })).toBeVisible()
  await expect(page.getByText('Country comparison')).toHaveCount(0)
})

test('switches country without a page reload', async ({ page }) => {
  const selector = page.getByLabel('Select country')
  await selector.selectOption('PRT')
  await expect(page.getByLabel('Select country')).toHaveValue('PRT')
  await expect(selector).toHaveValue('PRT')

  await selector.selectOption('IRL')
  await expect(page.getByLabel('Select country')).toHaveValue('IRL')
  await expect(selector).toHaveValue('IRL')
})

test('comparison remains neutral and aligned', async ({ page }) => {
  await page.getByRole('button', { name: 'Compare' }).click()
  await expect(page.getByRole('columnheader', { name: 'Spain' })).toBeVisible()
  await expect(page.getByRole('columnheader', { name: 'Portugal' })).toBeVisible()
  await expect(page.getByRole('columnheader', { name: 'Ireland' })).toBeVisible()
  await expect(page.getByText('aligned indicators · no ranking')).toBeVisible()
})


test('Indicators route exposes drill-down evidence', async ({ page }) => {
  await page.goto('/country/ESP/overview')
  await page.getByRole('button', { name: 'Indicators' }).click()

  await expect(page).toHaveURL(/\/country\/ESP\/indicators$/)
  await expect(page.getByRole('region', { name: 'Indicators' })).toBeVisible()
  await expect(page.getByText('Spain evidence')).toBeVisible()
  await expect(page.getByText('Unemployment, total (% of total labor force)', { exact: true })).toBeVisible()
})

test('Overview dimension cards drill into persistent dimension routes', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  await page.getByRole('button', { name: 'Open Productive capacity dimension' }).click()

  await expect(page).toHaveURL(/\/country\/ESP\/dimension\/productive_capacity$/)
  await expect(page.getByRole('region', { name: 'Dimension detail' })).toBeVisible()
  await expect(page.getByText('Productive capacity · Spain')).toBeVisible()
  await expect(page.getByText('Unemployment, total (% of total labor force)', { exact: true })).toBeVisible()

  await page.reload()

  await expect(page).toHaveURL(/\/country\/ESP\/dimension\/productive_capacity$/)
  await expect(page.getByRole('region', { name: 'Dimension detail' })).toBeVisible()

  await page.getByRole('button', { name: 'All indicators' }).click()
  await expect(page).toHaveURL(/\/country\/ESP\/indicators$/)
})


test('world view renders country geometry and drives selection', async ({ page }) => {
  await expect(page.getByText('WORLD VIEW')).toBeVisible()

  const map = page.getByTestId('world-map')
  await expect(map).toBeVisible()

  const portugalShape = map.locator('[data-country="PRT"]')
  await expect(portugalShape).toHaveCount(1)
  await expect(portugalShape).toBeVisible()

  await portugalShape.click()

  await expect(page.getByLabel('Select country')).toHaveValue('PRT')
  await expect(page).toHaveURL(/\/country\/PRT\/overview$/)
})


test('personal profile remains separate and can be saved locally', async ({ page }) => {
  await page.getByRole('button', { name: 'Profile' }).click()
  const profile = page.getByRole('region', { name: 'Personal profile' })
  await expect(profile.getByText('stored locally · never changes country facts')).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Profile completion' })).toBeVisible()
  await expect(profile.getByText('0 / 4 input sets ready')).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Personal-fit evidence' })).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Fit outputs' })).toBeVisible()
  await expect(profile.getByRole('region', { name: 'TTV readiness' })).toBeVisible()
  await expect(profile.getByText('PERSONAL-FIT EVIDENCE · ESP')).toBeVisible()
  await expect(profile.getByText('FIT OUTPUTS · ESP')).toBeVisible()
  await expect(profile.getByText('LegalFit', { exact: true }).first()).toBeVisible()
  await expect(profile.getByText('LanguageFit', { exact: true }).first()).toBeVisible()
  await expect(profile.getByText('CareerFit', { exact: true }).first()).toBeVisible()
  await expect(profile.getByText('FinancialFit', { exact: true }).first()).toBeVisible()
  await expect(profile.getByText('TTV READINESS · ESP')).toBeVisible()
  await expect(profile.getByText('Time estimate unavailable')).toBeVisible()

  await profile.getByLabel('Profession').fill('Systems engineer')
  await profile.getByLabel('Household size').fill('2')
  await profile.getByRole('button', { name: 'Save profile' }).click()

  await expect(profile.getByText('Saved locally')).toBeVisible()
})


test('profile marks future financial inputs that do not affect current FinancialFit', async ({ page }) => {
  await page.goto('/country/ESP/profile')

  const profile = page.getByRole('region', { name: 'Personal profile' })
  await expect(profile.getByText('Stored for future household-budget modelling; not used in current FinancialFit.')).toBeVisible()
  await expect(profile.getByText('Stored for future transition-cost/runway modelling; not used in current FinancialFit.')).toBeVisible()
})


test('profile architecture keeps completion evidence outputs and TTV distinct', async ({ page }) => {
  await page.goto('/country/ESP/profile')

  const profile = page.getByRole('region', { name: 'Personal profile' })
  await expect(profile.getByRole('region', { name: 'Profile inputs' })).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Profile completion' })).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Personal-fit evidence' })).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Fit outputs' })).toBeVisible()
  await expect(profile.getByRole('region', { name: 'TTV readiness' })).toBeVisible()

  await expect(profile.getByText('Completion only confirms that required profile inputs exist. It is not a country-fit score.')).toBeVisible()
  await expect(profile.getByText('Time-to-viability requires both viable dependencies and a validated temporal evidence model. Dependency readiness alone never creates a duration.')).toBeVisible()
})


test('latest EURES annex provenance is visible for unit-level CareerFit', async ({ page }) => {
  await page.route(
    'http://127.0.0.1:8020/api/countries/ESP/career-fit',
    async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          target_country_iso3: 'ESP',
          status: 'evidence_available',
          occupation: {
            status: 'mapped',
            occupation_group: 'information_communications_technicians',
            matched_terms: [],
            mapping_method: 'esco_isco_submajor',
            isco_submajor: '35',
          },
          market_signal: 'not_classified_as_shortage_or_surplus',
          market_signal_scope: 'isco_unit_group',
          market_signal_isco: '3512',
          vacancy_demand_evidence: null,
          occupation_match: {
            status: 'matched',
            threshold: 0.72,
            selected: {
              preferred_label: 'ICT user support technician',
              match_score: 0.91,
              match_method: 'token_overlap',
              source_mode: 'full',
              dataset_version: '1.2.1',
            },
            candidates: [],
          },
          skill_match: {
            status: 'matched',
            dataset_mode: 'full',
            dataset_version: '1.2.1',
            matched_skills: [],
            missing_skills: [],
            coverage: 1,
          },
          skill_evidence_complete: true,
          market_evidence_complete: true,
          evidence_complete: true,
          profile_skill_coverage_complete: true,
          market_signal_supports_viability: false,
          viability_evidence_ready: false,
          rule_version: 'EURES_SHORTAGES_SURPLUSES_2025_ANNEX',
          source: {
            label: 'EURES Report on labour shortages and surpluses 2025 — Annex',
            url: 'https://www.ela.europa.eu/en/publications/labour-shortages-and-surpluses-europe-2025',
            evidence_id: 'eures_shortages_surpluses_2025_annex',
            rule_version: 'EURES_SHORTAGES_SURPLUSES_2025_ANNEX',
            report_year: 2026,
            conditions_year: 2025,
            report_url: 'https://www.ela.europa.eu/sites/default/files/2026-06/annex-labour-shortages-report-ela-2025.pdf',
            scope: 'isco_unit_group',
          },
          notes: [],
        }),
      })
    },
  )

  await page.goto('/country/ESP/profile')

  const profile = page.getByRole('region', { name: 'Personal profile' })
  await expect(
    profile.getByText(
      'EURES 2026 · 2025 conditions · not classified as shortage or surplus · ISCO 3512 unit · eures_shortages_surpluses_2025_annex',
    ),
  ).toBeVisible()
})


test('vacancy rate remains contextual in Profile', async ({ page }) => {
  await page.goto('/country/ESP/profile')

  const profile = page.getByRole('region', { name: 'Personal profile' })
  await expect(
    profile.getByText(
      'Eurostat 2026-Q2 · ISCO OC3 vacancy rate 3.4% · context only',
    ),
  ).toBeVisible()
})


test('versioned EURES market evidence is visible in CareerFit', async ({ page }) => {
  await page.goto('/country/ESP/profile')

  const profile = page.getByRole('region', { name: 'Personal profile' })
  await expect(
    profile.getByText(
      'EURES 2025 · 2024 conditions · signal unavailable · eures_country_lmi_2024_conditions',
    ),
  ).toBeVisible()
})


test('structured FinancialFit blockers are visible', async ({ page }) => {
  await page.goto('/country/ESP/profile')

  const profile = page.getByRole('region', { name: 'Personal profile' })
  await expect(profile.getByText('FINANCIAL', { exact: true })).toBeVisible()
  await expect(profile.getByText('monthly net income', { exact: true })).toBeVisible()
})


test('structured TTV blockers are visible', async ({ page }) => {
  await page.goto('/country/ESP/profile')

  const ttv = page.getByRole('region', { name: 'TTV readiness' })
  await expect(ttv.getByText('Blocked by')).toBeVisible()
  await expect(ttv.locator('.ttvBlockedReason span')).not.toHaveText('Waiting for evidence')
})


test('candidate TTV range shows critical-path composition', async ({ page }) => {
  await page.route(
    'http://127.0.0.1:8020/api/countries/ESP/ttv',
    async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          target_country_iso3: 'ESP',
          method: 'ttv_dependency_graph_v1',
          stage_order: ['legal_fit', 'language_fit', 'career_fit', 'financial_fit'],
          stages: {
            legal_fit: { ready: true, status: 'eu_free_movement_framework', evidence_state: 'implemented' },
            language_fit: { ready: true, status: 'work_ready_heuristic', evidence_state: 'implemented' },
            career_fit: { ready: true, status: 'shortage', evidence_state: 'implemented' },
            financial_fit: { ready: true, status: 'portable_income_comparable', evidence_state: 'implemented' },
          },
          blocked_by: [],
          blocker_details: [],
          dependency_ready: true,
          temporal_evidence_state: 'not_implemented',
          temporal_model_version: null,
          temporal_evidence_ready: true,
          temporal_evidence: {
            engine_version: 'ttv-temporal-evidence-v1',
            calendar_ready: true,
            unavailable_stages: [],
            candidate_range: {
              weeks_min: 10,
              weeks_max: 25,
              composition: 'critical_path_v1',
              stage_groups: {
                preparation_parallel: ['legal', 'language', 'skills'],
                employment_after_preparation: ['employment'],
                financial_after_employment: ['financial'],
              },
            },
            stages: {
              legal: { status: 'available', weeks_min: 0, weeks_max: 0, reason: 'ready' },
              language: { status: 'available', weeks_min: 10, weeks_max: 25, reason: 'test' },
              skills: { status: 'available', weeks_min: 0, weeks_max: 0, reason: 'ready' },
              employment: { status: 'available', weeks_min: 0, weeks_max: 0, reason: 'ready' },
              financial: { status: 'available', weeks_min: 0, weeks_max: 0, reason: 'ready' },
            },
          },
          candidate_time_range: {
            weeks_min: 10,
            weeks_max: 25,
            composition: 'critical_path_v1',
            stage_groups: {
              preparation_parallel: ['legal', 'language', 'skills'],
              employment_after_preparation: ['employment'],
              financial_after_employment: ['financial'],
            },
          },
          estimate_status: 'temporal_model_missing',
          ready_for_time_estimate: false,
          time_estimate: null,
          notes: [],
        }),
      })
    },
  )

  await page.goto('/country/ESP/profile')

  const ttv = page.getByRole('region', { name: 'TTV readiness' })
  await expect(
    ttv.getByText(
      '10–25 weeks · critical path: preparation parallel → employment → financial · not an AUGUR estimate',
    ),
  ).toBeVisible()
  await expect(ttv.getByText('Estimate available')).toHaveCount(0)
})


test('candidate temporal evidence remains explicitly non-estimate', async ({ page }) => {
  await page.goto('/country/ESP/profile')

  const ttv = page.getByRole('region', { name: 'TTV readiness' })
  await expect(ttv.getByText('Temporal evidence · candidate only')).toBeVisible()
  await expect(ttv.getByText('Language: 100–250 guided hours · add study hours/week for calendar conversion')).toBeVisible()
  await expect(ttv.getByText('Estimate available')).toHaveCount(0)
})


test('map zoom controls change and reset the view', async ({ page }) => {
  const map = page.getByTestId('world-map')
  await expect(map).toBeVisible()

  const initialViewBox = await map.getAttribute('viewBox')

  await page.getByRole('button', { name: 'Zoom in' }).click()
  await expect.poll(async () => map.getAttribute('viewBox')).not.toBe(initialViewBox)

  await page.getByRole('button', { name: 'Reset map' }).click()
  await expect(map).toHaveAttribute('viewBox', initialViewBox ?? '0 0 1000 500')
})


test('unsaved profile edits survive target-country switching', async ({ page }) => {
  await page.getByRole('button', { name: 'Profile' }).click()
  const profile = page.getByRole('region', { name: 'Personal profile' })
  const profession = profile.getByLabel('Profession')
  const selector = page.getByLabel('Select country')

  await profession.fill('Unsaved draft role')
  await selector.selectOption('PRT')

  await expect(page.getByLabel('Select country')).toHaveValue('PRT')
  await expect(profession).toHaveValue('Unsaved draft role')
})


test('partial country endpoint failure keeps healthy sections visible', async ({ page }) => {
  await page.route('**/api/countries/PRT/scenarios', async route => {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'synthetic scenarios failure' }),
    })
  })

  await page.getByLabel('Select country').selectOption('PRT')

  await expect(page.getByLabel('Select country')).toHaveValue('PRT')
  await expect(page.getByText('KEY DIMENSIONS')).toBeVisible()
  await expect(page.getByText(/Scenarios HTTP 500/)).toBeVisible()
})


test('rapid country switching keeps the latest selection', async ({ page }) => {
  await page.route('**/api/countries/PRT/snapshot', async route => {
    await new Promise(resolve => setTimeout(resolve, 250))
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        country_iso3: 'PRT',
        observation_count: 1,
        indicators: [metric('PRT')],
      }),
    })
  })

  const selector = page.getByLabel('Select country')
  await selector.selectOption('PRT')
  await selector.selectOption('IRL')

  await expect(page.getByLabel('Select country')).toHaveValue('IRL')
  await expect(selector).toHaveValue('IRL')
})


test('unsaved profile draft survives view navigation', async ({ page }) => {
  await page.getByRole('button', { name: 'Profile' }).click()
  const profile = page.getByRole('region', { name: 'Personal profile' })
  const profession = profile.getByLabel('Profession')

  await profession.fill('Draft preserved across views')
  await page.getByRole('button', { name: 'Overview' }).click()
  await page.getByRole('button', { name: 'Profile' }).click()

  await expect(profession).toHaveValue('Draft preserved across views')
})

test('comparison selectors swap countries without duplicates', async ({ page }) => {
  await page.getByRole('button', { name: 'Compare' }).click()

  const first = page.getByLabel('Compare country 1', { exact: true })
  const second = page.getByLabel('Compare country 2', { exact: true })
  const third = page.getByLabel('Compare country 3', { exact: true })

  await expect(first).toHaveValue('IRL')
  await expect(second).toHaveValue('ESP')
  await expect(third).toHaveValue('PRT')

  await first.selectOption('ESP')

  await expect(first).toHaveValue('ESP')
  await expect(second).toHaveValue('IRL')
  await expect(third).toHaveValue('PRT')
})

test('guarded Edit Layout persists safe panel ordering', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/country/ESP/overview')

  await page.getByRole('button', { name: 'Edit layout' }).click()
  const controls = page.getByRole('region', { name: 'Dashboard layout settings' })
  await expect(controls).toBeVisible()
  await expect(controls.getByText('Core panels, approved proportions and responsive behaviour stay fixed.')).toBeVisible()
  await expect(controls.locator('input[type="range"]')).toHaveCount(0)
  await expect(controls.locator('input[type="checkbox"]')).toHaveCount(0)

  await controls.getByRole('button', { name: 'Fit · Map' }).click()
  await controls.getByRole('button', { name: 'Compare first' }).click()

  const reordered = await page.evaluate(() => ({
    mapLeft: document.querySelector('.overviewMapPanel')!.getBoundingClientRect().left,
    fitLeft: document.querySelector('.overviewFitPanel')!.getBoundingClientRect().left,
    outlookTop: document.querySelector('.overviewOutlookCard')!.getBoundingClientRect().top,
    compareTop: document.querySelector('.overviewCompareCard')!.getBoundingClientRect().top,
  }))

  expect(reordered.fitLeft).toBeLessThan(reordered.mapLeft)
  expect(reordered.compareTop).toBeLessThan(reordered.outlookTop)

  await page.reload()

  const persisted = await page.evaluate(() => ({
    mapLeft: document.querySelector('.overviewMapPanel')!.getBoundingClientRect().left,
    fitLeft: document.querySelector('.overviewFitPanel')!.getBoundingClientRect().left,
    outlookTop: document.querySelector('.overviewOutlookCard')!.getBoundingClientRect().top,
    compareTop: document.querySelector('.overviewCompareCard')!.getBoundingClientRect().top,
  }))

  expect(persisted.fitLeft).toBeLessThan(persisted.mapLeft)
  expect(persisted.compareTop).toBeLessThan(persisted.outlookTop)

  await page.getByRole('button', { name: 'Edit layout' }).click()
  await page.getByRole('region', { name: 'Dashboard layout settings' }).getByRole('button', { name: 'Reset layout' }).click()

  const reset = await page.evaluate(() => ({
    mapLeft: document.querySelector('.overviewMapPanel')!.getBoundingClientRect().left,
    fitLeft: document.querySelector('.overviewFitPanel')!.getBoundingClientRect().left,
    outlookTop: document.querySelector('.overviewOutlookCard')!.getBoundingClientRect().top,
    compareTop: document.querySelector('.overviewCompareCard')!.getBoundingClientRect().top,
  }))

  expect(reset.mapLeft).toBeLessThan(reset.fitLeft)
  expect(reset.outlookTop).toBeLessThan(reset.compareTop)
})


test('direct route refresh preserves country and view', async ({ page }) => {
  await page.goto('/country/PRT/outlook')
  await expect(page.getByLabel('Select country')).toHaveValue('PRT')
  await expect(page.getByText('OFFICIAL OUTLOOK')).toBeVisible()
  await expect(page.getByTestId('world-map')).toHaveCount(0)

  await page.reload()

  await expect(page).toHaveURL(/\/country\/PRT\/outlook$/)
  await expect(page.getByLabel('Select country')).toHaveValue('PRT')
  await expect(page.getByText('OFFICIAL OUTLOOK')).toBeVisible()
})

test('compare selection is encoded in URL and survives reload', async ({ page }) => {
  await page.goto('/compare?countries=ESP,PRT,IRL')

  await expect(page.getByLabel('Compare country 1', { exact: true })).toHaveValue('ESP')
  await expect(page.getByLabel('Compare country 2', { exact: true })).toHaveValue('PRT')
  await expect(page.getByLabel('Compare country 3', { exact: true })).toHaveValue('IRL')

  await page.getByLabel('Compare country 1', { exact: true }).selectOption('IRL')
  await expect(page).toHaveURL(/countries=IRL,PRT,ESP|countries=IRL%2CPRT%2CESP/)

  await page.reload()

  await expect(page.getByLabel('Compare country 1', { exact: true })).toHaveValue('IRL')
  await expect(page.getByLabel('Compare country 2', { exact: true })).toHaveValue('PRT')
  await expect(page.getByLabel('Compare country 3', { exact: true })).toHaveValue('ESP')
})


test('frozen-spec Overview renders the approved composition', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/country/ESP/overview')

  await expect(page.getByRole('region', { name: 'Country overview' })).toBeVisible()
  await expect(page.getByTestId('world-map')).toBeVisible()
  await expect(page.getByRole('region', { name: 'Personal fit snapshot' })).toBeVisible()
  await expect(page.getByText('KEY DIMENSIONS')).toBeVisible()
  await expect(page.locator('.overviewInsightRail .overallSignalBalance')).toBeVisible()
  await expect(page.locator('.overviewOutlookCard')).toBeVisible()
  await expect(page.locator('.overviewCompareCard')).toBeVisible()

  const layout = await page.evaluate(() => {
    const rect = (selector: string) => {
      const node = document.querySelector(selector)
      if (!node) return null
      const box = node.getBoundingClientRect()
      return { left: box.left, right: box.right, top: box.top, bottom: box.bottom, width: box.width }
    }

    return {
      map: rect('.overviewMapPanel'),
      fit: rect('.overviewFitPanel'),
      dimensions: rect('.overviewDimensionsPanel'),
      rail: rect('.overviewInsightRail'),
      scrollHeight: document.documentElement.scrollHeight,
      innerHeight: window.innerHeight,
    }
  })

  expect(layout.map).not.toBeNull()
  expect(layout.fit).not.toBeNull()
  expect(layout.dimensions).not.toBeNull()
  expect(layout.rail).not.toBeNull()

  expect(layout.map!.left).toBeLessThan(layout.fit!.left)
  expect(layout.dimensions!.left).toBeLessThan(layout.rail!.left)

  const topRatio = layout.map!.width / (layout.map!.width + layout.fit!.width)
  const bottomRatio = layout.dimensions!.width / (layout.dimensions!.width + layout.rail!.width)

  expect(topRatio).toBeGreaterThan(0.53)
  expect(topRatio).toBeLessThan(0.59)
  expect(bottomRatio).toBeGreaterThan(0.72)
  expect(bottomRatio).toBeLessThan(0.78)

  expect(layout.scrollHeight).toBeLessThanOrEqual(layout.innerHeight + 2)
})

test('Overview panels do not overlap at 1920x1080', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/country/ESP/overview')

  const boxes = await page.evaluate(() => {
    const box = (selector: string) => {
      const node = document.querySelector(selector)
      if (!node) return null
      const rect = node.getBoundingClientRect()
      return { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom }
    }

    return {
      map: box('.overviewMapPanel'),
      fit: box('.overviewFitPanel'),
      dimensions: box('.overviewDimensionsPanel'),
      assessment: box('.overviewInsightRail .overallSignalBalance'),
      outlook: box('.overviewOutlookCard'),
      compare: box('.overviewCompareCard'),
    }
  })

  const overlaps = (
    a: { left: number; right: number; top: number; bottom: number },
    b: { left: number; right: number; top: number; bottom: number },
  ) => !(
    a.right <= b.left ||
    b.right <= a.left ||
    a.bottom <= b.top ||
    b.bottom <= a.top
  )

  for (const value of Object.values(boxes)) expect(value).not.toBeNull()

  expect(overlaps(boxes.map!, boxes.fit!)).toBe(false)
  expect(overlaps(boxes.dimensions!, boxes.assessment!)).toBe(false)
  expect(overlaps(boxes.dimensions!, boxes.outlook!)).toBe(false)
  expect(overlaps(boxes.dimensions!, boxes.compare!)).toBe(false)
  expect(overlaps(boxes.assessment!, boxes.outlook!)).toBe(false)
  expect(overlaps(boxes.outlook!, boxes.compare!)).toBe(false)
})

test('Overview country flags and fit readiness remain visible', async ({ page }) => {
  await page.goto('/country/ESP/overview')

  await expect(page.locator('.worldMapLegend .flagIcon')).toHaveCount(3)
  await expect(page.locator('.topbarCountry .flagIcon')).toHaveCount(1)
  await expect(page.locator('.readinessRing')).toHaveCount(5)
  await expect(page.locator('.compareBarTrack')).toHaveCount(3)
})


test('responsive shell avoids horizontal overflow across core views', async ({ page }) => {
  const cases = [
    { width: 1366, height: 768 },
    { width: 1024, height: 768 },
    { width: 390, height: 844 },
  ]

  for (const viewport of cases) {
    await page.setViewportSize(viewport)

    for (const path of [
      '/country/ESP/overview',
      '/country/ESP/indicators',
      '/country/ESP/dimension/productive_capacity',
      '/country/ESP/outlook',
      '/country/ESP/profile',
      '/compare?countries=ESP,PRT,IRL',
    ]) {
      await page.goto(path)
      await expect(page.locator('main.shell')).toBeVisible()

      const overflow = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
      }))

      expect(
        overflow.scrollWidth,
        `horizontal overflow at ${viewport.width}x${viewport.height} on ${path}`,
      ).toBeLessThanOrEqual(overflow.innerWidth + 2)
    }
  }
})

test('overview keeps last-row content inside desktop viewport', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/country/ESP/overview')

  const viewportHeight = await page.evaluate(() => window.innerHeight)

  const cards = page.locator('.overviewDimensionGridV2 .mockDimensionCard')
  const lastCard = cards.last()
  const compareCard = page.locator('.overviewCompareCard')

  const [lastBox, compareBox] = await Promise.all([
    lastCard.boundingBox(),
    compareCard.boundingBox(),
  ])

  expect(lastBox).not.toBeNull()
  expect(compareBox).not.toBeNull()

  expect((lastBox?.y ?? 0) + (lastBox?.height ?? 0)).toBeLessThanOrEqual(
    viewportHeight - 4,
  )
  expect((compareBox?.y ?? 0) + (compareBox?.height ?? 0)).toBeLessThanOrEqual(
    viewportHeight - 4,
  )

  const clipped = await page.evaluate(() => {
    const selectors = [
      '.overviewDimensionGridV2 .mockDimensionCard',
      '.overviewCompareCard',
      '.overviewOutlookCard',
      '.overallSignalBalance',
    ]
    return selectors.flatMap(selector =>
      Array.from(document.querySelectorAll<HTMLElement>(selector))
        .filter(el => {
          const rect = el.getBoundingClientRect()
          return rect.bottom > window.innerHeight || rect.right > window.innerWidth
        })
        .map(el => selector),
    )
  })

  expect(clipped).toEqual([])
})


test('responsive Overview preserves every frozen core panel', async ({ page }) => {
  for (const viewport of [
    { width: 1366, height: 768 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport)
    await page.goto('/country/ESP/overview')

    await expect(page.getByTestId('world-map')).toBeVisible()
    await expect(page.getByRole('region', { name: 'Personal fit snapshot' })).toBeVisible()
    await expect(page.getByText('KEY DIMENSIONS')).toBeVisible()
    await expect(page.locator('.overviewInsightRail .overallSignalBalance')).toBeVisible()
    await expect(page.locator('.overviewOutlookCard')).toBeVisible()
    await expect(page.locator('.overviewCompareCard')).toBeVisible()
  }
})

test('mobile Profile keeps its five information layers reachable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/country/ESP/profile')

  const profile = page.getByRole('region', { name: 'Personal profile' })
  await expect(profile.getByRole('region', { name: 'Profile inputs' })).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Profile completion' })).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Personal-fit evidence' })).toBeVisible()
  await expect(profile.getByRole('region', { name: 'Fit outputs' })).toBeVisible()
  await expect(profile.getByRole('region', { name: 'TTV readiness' })).toBeVisible()
})
