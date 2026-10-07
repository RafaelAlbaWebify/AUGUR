import { useEffect, useRef, useState } from 'react'
import './profile-page.css'

type LanguageSkill = {
  language: string
  cefr: string | null
}

type PersonalProfile = {
  profile_id?: string
  age: number | null
  current_country: string | null
  citizenships: string[]
  profession: string | null
  skills: string[]
  languages: LanguageSkill[]
  household_size: number
  monthly_net_income: number | null
  liquid_savings: number | null
  remote_work: boolean
  preferences: Record<string, string | number | boolean>
  updated_at?: string | null
}

type ReadinessModule = {
  label: string
  ready: boolean
  completed_fields: number
  required_fields: number
  missing_fields: string[]
}

type ReadinessResponse = {
  profile_id: string
  modules: Record<string, ReadinessModule>
  ready_module_count: number
  module_count: number
  notes: string[]
}

type LegalFitResponse = {
  target_country_iso3: string
  status: string
  framework: string | null
  work_permit_required: boolean | null
  basis_citizenships?: string[]
  short_stay: null | {
    up_to_months: number
    residence_registration_generally_required: boolean
    presence_reporting_may_apply: boolean
  }
  long_stay: null | {
    registration_may_be_required: boolean
    conditions_depend_on_status: boolean
    statuses: string[]
  }
  rule_version: string
  notes: string[]
}

type LanguageFitResponse = {
  target_country_iso3: string
  status: string
  target_languages: string[]
  matches: Array<{
    language: string
    declared_cefr: string | null
    meets_work_ready_heuristic: boolean
  }>
  work_ready_threshold: string
  work_ready: boolean
  method: string
  occupation_language_evidence?: {
    status: string
    occupation_label: string | null
    dataset_mode: string | null
    dataset_version: string | null
    skills: Array<{
      skill_uri: string
      skill_label: string
      relation_type: string
    }>
    essential_skill_count: number
    optional_skill_count: number
    evidence_complete: boolean
  }
  notes: string[]
}

type CareerFitResponse = {
  target_country_iso3: string
  status: string
  occupation: {
    status: string
    occupation_group: string | null
    matched_terms: string[]
    mapping_method?: string
    isco_submajor?: string | null
  }
  market_signal: string | null
  market_signal_scope?: string
  market_signal_isco?: string | null
  vacancy_demand_evidence?: null | {
    status: string
    isco_major: string
    vacancy_rate_pct?: number
    period?: string
    nace_scope?: string | null
    source_id?: string
    dataset_id?: string
    granularity: string
    role: string
  }
  occupation_match?: {
    status: string
    threshold: number
    selected: null | {
      preferred_label: string
      match_score: number
      match_method: string
      source_mode?: string
      dataset_version?: string
    }
    candidates: Array<{
      preferred_label: string
      match_score: number
      match_method: string
    }>
  }
  skill_match: {
    status: string
    dataset_mode?: string | null
    dataset_version?: string | null
    matched_skills: string[]
    missing_skills: string[]
    coverage?: number | null
  }
  skill_evidence_complete?: boolean
  market_evidence_complete?: boolean
  evidence_complete: boolean
  profile_skill_coverage_complete?: boolean
  market_signal_supports_viability?: boolean
  viability_evidence_ready?: boolean
  rule_version: string
  source: null | {
    label: string
    url: string
    evidence_id?: string
    rule_version?: string
    report_year?: number
    conditions_year?: number
    report_url?: string
    scope?: string
  }
  notes: string[]
}

type FinancialFitResponse = {
  target_country_iso3: string
  status: string
  reason: string | null
  evidence_state?: string
  evidence_complete?: boolean
  blockers?: string[]
  local_income_reference?: null | {
    occupation_label: string
    occupation_match_score: number
    isco_group: string
    ses_isco_major_group: string
    gross_monthly_mean_eur: number
    period: number
    source_id: string
    dataset_id: string
    source_updated_at?: string | null
  }
  national_net_earnings_reference?: null | {
    earnings_case: string
    annual_net_eur: number
    monthly_net_equivalent_eur: number
    period: number
    source_id: string
    dataset_id: string
    source_updated_at?: string | null
    scope: string
  }
  portable_income_analysis: null | {
    origin_country_iso3: string
    monthly_net_income: number
    origin_price_level_index: number
    origin_period: number
    target_price_level_index: number
    target_period: number
    relative_cost_factor: number
    origin_equivalent_purchasing_power: number
    purchasing_power_change_pct: number
    source_id: string
  }
  notes: string[]
}

type TTVStage = {
  ready: boolean
  status: string
  evidence_state: string
  reason?: string
}

type TTVResponse = {
  target_country_iso3: string
  method: string
  stage_order: string[]
  stages: Record<string, TTVStage>
  blocked_by: string[]
  blocker_details?: Array<{
    stage_id: string
    status: string
    evidence_state: string
    reason?: string
  }>
  dependency_ready?: boolean
  temporal_evidence_state?: string
  temporal_model_version?: string | null
  temporal_evidence_ready?: boolean
  temporal_evidence?: {
    engine_version: string
    calendar_ready: boolean
    estimation_scope?: {
      scope_id: string
      in_scope: boolean
      blockers: string[]
    }
    unavailable_stages: string[]
    candidate_range: null | {
      weeks_min: number
      weeks_max: number
      composition: string
      stage_groups?: {
        preparation_parallel: string[]
        employment_after_preparation: string[]
        financial_after_employment: string[]
      }
    }
    stages: Record<string, {
      status: string
      weeks_min: number | null
      weeks_max: number | null
      reason: string
      guided_hours_min?: number | null
      guided_hours_max?: number | null
      weekly_study_hours?: number | null
      current_cefr?: string | null
      target_cefr?: string | null
    }>
  }
  candidate_time_range?: null | {
    weeks_min: number
    weeks_max: number
    composition: string
    stage_groups?: {
      preparation_parallel: string[]
      employment_after_preparation: string[]
      financial_after_employment: string[]
    }
  }
  estimate_status?: string
  ready_for_time_estimate: boolean
  time_estimate: null
  notes: string[]
}

type TTVCalibrationStatus = {
  protocol_state: string
  protocol_version: string | null
  development_case_count: number
  holdout_case_count: number
  interval_coverage_pct: number | null
  mean_interval_width_weeks: number | null
  mean_absolute_midpoint_error_weeks: number | null
  mean_miss_distance_weeks: number | null
  context_summary: {
    context_case_count: number
    current_cefr_levels: string[]
    target_cefr_levels: string[]
    weekly_study_hours: number[]
  }
  protocol_readiness?: {
    blockers: string[]
  }
}

type TTVCalibrationObservation = {
  case_id: string
  country_iso3: string
  status: 'active' | 'completed' | 'cancelled'
  scope_id: string
  engine_version: string
  composition: string
  candidate_weeks_min: number
  candidate_weeks_max: number
  started_at: string
  completed_at?: string | null
  baseline: {
    target_country_iso3?: string
    language?: {
      current_cefr?: string | null
      target_cefr?: string | null
      weekly_study_hours?: number | null
      guided_hours_min?: number | null
      guided_hours_max?: number | null
    }
  }
  completion?: Record<string, unknown>
}

type ProfilePanelProps = {
  apiBase: string
  targetCountry: string
}

type ProfileDraftCache = {
  profile: PersonalProfile
  citizenshipsText: string
  skillsText: string
  languagesText: string
}

let profileDraftCache: ProfileDraftCache | null = null

const EMPTY_PROFILE: PersonalProfile = {
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
}

function parseList(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function parseLanguages(value: string): LanguageSkill[] {
  return parseList(value).map((item) => {
    const [language, cefr] = item.split(':').map((part) => part.trim())
    return {
      language,
      cefr: cefr || null,
    }
  })
}

function formatLanguages(languages: LanguageSkill[]) {
  return languages
    .map((item) => item.cefr ? `${item.language}:${item.cefr}` : item.language)
    .join(', ')
}

const DECISION_WEIGHT_DIMENSIONS = [
  ['human_systems', 'Human systems'],
  ['prosperity', 'Prosperity'],
  ['infrastructure', 'Infrastructure'],
  ['safety', 'Safety'],
  ['environment', 'Environment'],
  ['housing', 'Housing'],
  ['strategic_resilience', 'Strategic resilience'],
  ['demography', 'Demography'],
  ['productive_capacity', 'Productive capacity'],
  ['fiscal', 'Fiscal sustainability'],
] as const

export default function ProfilePanel({ apiBase, targetCountry }: ProfilePanelProps) {
  const [profile, setProfile] = useState<PersonalProfile>(
    () => profileDraftCache?.profile ?? EMPTY_PROFILE,
  )
  const [citizenshipsText, setCitizenshipsText] = useState(
    () => profileDraftCache?.citizenshipsText ?? '',
  )
  const [skillsText, setSkillsText] = useState(
    () => profileDraftCache?.skillsText ?? '',
  )
  const [languagesText, setLanguagesText] = useState(
    () => profileDraftCache?.languagesText ?? '',
  )
  const [status, setStatus] = useState<'loading' | 'ready' | 'saving' | 'saved' | 'error'>(
    () => profileDraftCache ? 'ready' : 'loading',
  )
  const [editMode, setEditMode] = useState(false)
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null)
  const [financialFit, setFinancialFit] = useState<FinancialFitResponse | null>(null)
  const [legalFit, setLegalFit] = useState<LegalFitResponse | null>(null)
  const [languageFit, setLanguageFit] = useState<LanguageFitResponse | null>(null)
  const [careerFit, setCareerFit] = useState<CareerFitResponse | null>(null)
  const [ttv, setTtv] = useState<TTVResponse | null>(null)
  const [ttvObservation, setTtvObservation] = useState<TTVCalibrationObservation | null>(null)
  const [ttvCalibrationStatus, setTtvCalibrationStatus] = useState<TTVCalibrationStatus | null>(null)
  const [ttvObservationStatus, setTtvObservationStatus] = useState<'idle' | 'loading' | 'working' | 'error'>('idle')
  const [ttvExchangeStatus, setTtvExchangeStatus] = useState<'idle' | 'working' | 'saved' | 'imported' | 'error'>('idle')
  const fitRequestIdRef = useRef(0)

  useEffect(() => {
    profileDraftCache = {
      profile,
      citizenshipsText,
      skillsText,
      languagesText,
    }
  }, [profile, citizenshipsText, skillsText, languagesText])

  async function refreshTargetFits() {
    const requestId = ++fitRequestIdRef.current

    try {
      const [legalResponse, languageResponse, careerResponse, financialResponse, ttvResponse] = await Promise.all([
        fetch(`${apiBase}/api/countries/${targetCountry}/legal-fit`),
        fetch(`${apiBase}/api/countries/${targetCountry}/language-fit`),
        fetch(`${apiBase}/api/countries/${targetCountry}/career-fit`),
        fetch(`${apiBase}/api/countries/${targetCountry}/financial-fit`),
        fetch(`${apiBase}/api/countries/${targetCountry}/ttv`),
      ])

      if (
        !legalResponse.ok ||
        !languageResponse.ok ||
        !careerResponse.ok ||
        !financialResponse.ok ||
        !ttvResponse.ok ||
        requestId !== fitRequestIdRef.current
      ) {
        return
      }

      const [legalData, languageData, careerData, financialData, ttvData] = await Promise.all([
        legalResponse.json(),
        languageResponse.json(),
        careerResponse.json(),
        financialResponse.json(),
        ttvResponse.json(),
      ])

      if (requestId !== fitRequestIdRef.current) return

      setLegalFit(legalData)
      setLanguageFit(languageData)
      setCareerFit(careerData)
      setFinancialFit(financialData)
      setTtv(ttvData)
    } catch {
      // Profile editing remains usable if target-fit analysis cannot be loaded.
    }
  }

  async function refreshTtvCalibrationStatus() {
    try {
      const response = await fetch(`${apiBase}/api/ttv/calibration/status`)
      if (!response.ok) return
      setTtvCalibrationStatus(await response.json())
    } catch {
      // TTV fit remains usable when calibration diagnostics are unavailable.
    }
  }

  async function refreshTtvObservation() {
    setTtvObservationStatus('loading')
    try {
      const response = await fetch(
        `${apiBase}/api/countries/${targetCountry}/ttv/calibration/active`,
      )
      if (!response.ok) throw new Error(`TTV calibration HTTP ${response.status}`)
      const data = await response.json() as {
        observation: TTVCalibrationObservation | null
      }
      setTtvObservation(data.observation)
      setTtvObservationStatus('idle')
    } catch {
      setTtvObservationStatus('error')
    }
  }

  async function startTtvObservation() {
    setTtvObservationStatus('working')
    try {
      const response = await fetch(
        `${apiBase}/api/countries/${targetCountry}/ttv/calibration/start`,
        { method: 'POST' },
      )
      if (!response.ok) throw new Error(`TTV calibration HTTP ${response.status}`)
      const data = await response.json() as {
        observation: TTVCalibrationObservation
      }
      setTtvObservation(data.observation)
      setTtvObservationStatus('idle')
    } catch {
      setTtvObservationStatus('error')
    }
  }

  async function completeTtvObservation() {
    if (!ttvObservation) return
    setTtvObservationStatus('working')
    try {
      const response = await fetch(
        `${apiBase}/api/ttv/calibration/${ttvObservation.case_id}/complete`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ observed_at: null }),
        },
      )
      if (!response.ok) throw new Error(`TTV calibration HTTP ${response.status}`)
      setTtvObservation(null)
      setTtvObservationStatus('idle')
      await refreshTtvCalibrationStatus()
    } catch {
      setTtvObservationStatus('error')
    }
  }

  async function cancelTtvObservation() {
    if (!ttvObservation) return
    setTtvObservationStatus('working')
    try {
      const response = await fetch(
        `${apiBase}/api/ttv/calibration/${ttvObservation.case_id}/cancel`,
        { method: 'POST' },
      )
      if (!response.ok) throw new Error(`TTV calibration HTTP ${response.status}`)
      setTtvObservation(null)
      setTtvObservationStatus('idle')
    } catch {
      setTtvObservationStatus('error')
    }
  }

  async function exportTtvDevelopmentData() {
    setTtvExchangeStatus('working')
    try {
      const response = await fetch(`${apiBase}/api/ttv/calibration/export`)
      if (!response.ok) throw new Error(`TTV exchange HTTP ${response.status}`)
      const data = await response.json()
      const blob = new Blob(
        [JSON.stringify(data, null, 2)],
        { type: 'application/json' },
      )
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = 'AUGUR_TTV_DEVELOPMENT_EXCHANGE.json'
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      URL.revokeObjectURL(url)
      setTtvExchangeStatus('saved')
    } catch {
      setTtvExchangeStatus('error')
    }
  }

  async function importTtvDevelopmentData(file: File) {
    setTtvExchangeStatus('working')
    try {
      const text = await file.text()
      const payload = JSON.parse(text)
      const response = await fetch(
        `${apiBase}/api/ttv/calibration/import`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        },
      )
      if (!response.ok) throw new Error(`TTV exchange HTTP ${response.status}`)
      setTtvExchangeStatus('imported')
      await refreshTtvCalibrationStatus()
    } catch {
      setTtvExchangeStatus('error')
    }
  }

  async function refreshReadiness() {
    try {
      const response = await fetch(`${apiBase}/api/profile/readiness`)
      if (!response.ok) return
      setReadiness(await response.json())
    } catch {
      // Profile editing remains usable if readiness cannot be loaded.
    }
  }

  useEffect(() => {
    if (profileDraftCache) {
      setStatus('ready')
      void refreshReadiness()
      return
    }

    let active = true

    fetch(`${apiBase}/api/profile`)
      .then(async (response) => {
        if (!response.ok) throw new Error(`Profile HTTP ${response.status}`)
        return response.json()
      })
      .then((data: PersonalProfile) => {
        if (!active) return

        setProfile(data)
        setCitizenshipsText(data.citizenships.join(', '))
        setSkillsText(data.skills.join(', '))
        setLanguagesText(formatLanguages(data.languages))
        setStatus('ready')
        void refreshReadiness()
      })
      .catch(() => {
        if (active) setStatus('error')
      })

    return () => {
      active = false
    }
  }, [apiBase])

  useEffect(() => {
    setLegalFit(null)
    setLanguageFit(null)
    setCareerFit(null)
    setFinancialFit(null)
    setTtv(null)
    setTtvObservation(null)
    void refreshTargetFits()
    void refreshTtvObservation()
    void refreshTtvCalibrationStatus()
  }, [apiBase, targetCountry])

  async function save() {
    setStatus('saving')

    const payload = {
      ...profile,
      current_country: profile.current_country?.trim().toUpperCase() || null,
      citizenships: parseList(citizenshipsText).map((item) => item.toUpperCase()),
      skills: parseList(skillsText),
      languages: parseLanguages(languagesText),
    }

    delete payload.profile_id
    delete payload.updated_at

    try {
      const response = await fetch(`${apiBase}/api/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) throw new Error(`Profile HTTP ${response.status}`)

      const saved = await response.json() as PersonalProfile
      setProfile(saved)
      profileDraftCache = {
        profile: saved,
        citizenshipsText: saved.citizenships.join(', '),
        skillsText: saved.skills.join(', '),
        languagesText: formatLanguages(saved.languages),
      }
      setStatus('saved')
      await refreshReadiness()
      await refreshTargetFits()
    } catch {
      setStatus('error')
    }
  }

  const completionItems = Object.entries(readiness?.modules ?? {})
  const evidenceItems = [
    {
      id: 'legal',
      readinessKey: 'legal_fit',
      label: 'LegalFit',
      state: !legalFit || legalFit.status === 'insufficient_profile'
        ? 'incomplete'
        : legalFit.status === 'country_specific_rules_required'
        ? 'partial'
        : 'complete',
      detail: legalFit?.status?.replaceAll('_', ' ') ?? 'loading',
      decision: 'Work / residence feasibility',
      constraint: readiness?.modules?.legal_fit?.ready
        ? (legalFit?.status === 'country_specific_rules_required' ? 'country evidence' : 'resolved evidence')
        : 'profile input',
    },
    {
      id: 'language',
      readinessKey: 'language_fit',
      label: 'LanguageFit',
      state: !languageFit || languageFit.status === 'target_language_missing'
        ? 'incomplete'
        : 'complete',
      detail: languageFit?.status?.replaceAll('_', ' ') ?? 'loading',
      decision: 'Language viability',
      constraint: readiness?.modules?.language_fit?.ready
        ? (languageFit?.status === 'target_language_missing' ? 'target-country evidence' : 'resolved evidence')
        : 'profile input',
    },
    {
      id: 'career',
      readinessKey: 'career_fit',
      label: 'CareerFit',
      state: !careerFit || careerFit.status === 'profession_missing'
        ? 'incomplete'
        : careerFit.evidence_complete
        ? 'complete'
        : 'partial',
      detail: careerFit?.status?.replaceAll('_', ' ') ?? 'loading',
      decision: 'Career viability',
      constraint: readiness?.modules?.career_fit?.ready
        ? (careerFit?.evidence_complete ? 'resolved evidence' : 'market evidence')
        : 'profile input',
    },
    {
      id: 'financial',
      readinessKey: 'financial_fit',
      label: 'FinancialFit',
      state: !financialFit
        ? 'incomplete'
        : financialFit.evidence_complete
        ? 'complete'
        : financialFit.evidence_state === 'partial'
        ? 'partial'
        : 'incomplete',
      detail: financialFit?.status?.replaceAll('_', ' ') ?? 'loading',
      decision: 'Purchasing-power viability',
      constraint: readiness?.modules?.financial_fit?.ready
        ? (financialFit?.evidence_complete ? 'resolved evidence' : 'financial evidence')
        : 'profile input',
    },
  ]

  const priorityOptions = [
    { key: 'healthcare', label: 'Good healthcare', icon: '✚', description: 'Access, outcomes and system quality' },
    { key: 'safety', label: 'Safe environment', icon: '◇', description: 'Objective and perceived safety' },
    { key: 'climate', label: 'Mild climate', icon: '☼', description: 'Climate comfort and exposure' },
    { key: 'housing', label: 'Reasonable housing costs', icon: '⌂', description: 'Affordability relative to income' },
    { key: 'career', label: 'Career opportunities', icon: '↗', description: 'Demand, skills and earnings' },
    { key: 'mobility', label: 'EU mobility', icon: '↔', description: 'Legal access and ease of movement' },
  ] as const

  function togglePriority(key: string) {
    const preferences = { ...profile.preferences }
    const storageKey = `priority_${key}`
    if (preferences[storageKey] === true) delete preferences[storageKey]
    else preferences[storageKey] = true
    setProfile({ ...profile, preferences })
  }

  const gaps = completionItems.filter(([, item]) => !item.ready)
  const studyHours = typeof profile.preferences.language_study_hours_per_week === 'number'
    ? profile.preferences.language_study_hours_per_week
    : null
  const selectedPriorityCount = priorityOptions.filter(
    (item) => profile.preferences[`priority_${item.key}`] === true,
  ).length
  const selectedDecisionWeightCount = DECISION_WEIGHT_DIMENSIONS.filter(
    ([dimension]) => typeof profile.preferences[`decision_weight_${dimension}`] === 'number',
  ).length

  const gapPurpose: Record<string, string> = {
    legal_fit: 'work and residence evidence',
    career_fit: 'occupation and skill evidence',
    language_fit: 'language viability evidence',
    financial_fit: 'income and purchasing-power evidence',
  }

  const gapDecision: Record<string, string> = {
    legal_fit: 'Unlocks work / residence feasibility',
    career_fit: 'Unlocks career viability',
    language_fit: 'Unlocks language viability',
    financial_fit: 'Unlocks purchasing-power viability',
  }

  const ttvLanguageStage = ttv?.temporal_evidence?.stages?.language
  const ttvCalibrationEligible = Boolean(
    ttv?.candidate_time_range
    && ttv?.temporal_evidence?.calendar_ready
    && ttv?.temporal_evidence?.estimation_scope?.in_scope
    && ttvLanguageStage
    && (ttvLanguageStage.weeks_max ?? 0) > 0
  )

  return (
    <section className="profilePageV3" aria-label="Personal profile">
      <header className="myFitHeader">
        <div>
          <span>5. MY FIT / Profile</span>
          <h2>Your profile, gaps and actionable recommendations</h2>
        </div>
        <p>Build your profile to improve personal-fit evidence for {targetCountry}.</p>
      </header>

      <section className="myFitDecisionReadiness" aria-label="Personal-fit decision readiness">
        <div>
          <span>DECISION READINESS</span>
          <strong>{readiness ? `${readiness.ready_module_count}/${readiness.module_count} profile modules ready` : 'Checking profile inputs…'}</strong>
        </div>
        <div className="myFitDecisionModules">
          {evidenceItems.map((item) => (
            <article className={item.state} key={item.id}>
              <span>{item.label.replace('Fit', '')}</span>
              <strong>{item.decision}</strong>
              <small>{item.constraint}</small>
            </article>
          ))}
        </div>
        <p>Readiness is not a country score. It separates missing profile inputs from unresolved external evidence.</p>
      </section>

      <div className="myFitTopGrid">
        <section className="myFitCard profileSummaryCard">
          <div className="myFitCardHeader">
            <h3>Your profile</h3>
            <button type="button" onClick={() => setEditMode((value) => !value)}>
              {editMode ? 'Close edit' : 'Edit'}
            </button>
          </div>
          <dl className="profileSummaryList">
            <div><dt>Age</dt><dd>{profile.age ?? 'Not set'}</dd></div>
            <div><dt>Current country</dt><dd>{profile.current_country ?? 'Not set'}</dd></div>
            <div><dt>Citizenships</dt><dd>{profile.citizenships.length ? profile.citizenships.join(', ') : 'Not set'}</dd></div>
            <div><dt>Profession</dt><dd>{profile.profession ?? 'Not set'}</dd></div>
            <div><dt>Key skills</dt><dd>{profile.skills.length ? profile.skills.join(', ') : 'Not set'}</dd></div>
            <div><dt>Languages</dt><dd>{profile.languages.length ? profile.languages.map((item) => item.cefr ? `${item.language} (${item.cefr})` : item.language).join(', ') : 'Not set'}</dd></div>
            <div><dt>Study hours / week</dt><dd>{studyHours ?? 'Not set'}</dd></div>
            <div><dt>Monthly net income</dt><dd>{profile.monthly_net_income == null ? 'Not set' : `€${new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(profile.monthly_net_income)}`}</dd></div>
          </dl>
          <span className={`profileStatusBadge ${status === 'saved' ? 'saved' : status === 'error' ? 'error' : 'draft'}`}>
            {status === 'saved' ? 'Saved locally' : status === 'error' ? 'Save unavailable' : 'Local draft'}
          </span>
        </section>

        <section className="myFitCard" role="region" aria-label="Profile completion">
          <div className="myFitCardHeader">
            <h3>Profile completion</h3>
            <strong>{readiness ? `${readiness.ready_module_count} / ${readiness.module_count} input sets ready` : 'Checking…'}</strong>
          </div>
          <div className="completionMeter" aria-hidden="true">
            <i style={{ width: readiness && readiness.module_count ? `${(readiness.ready_module_count / readiness.module_count) * 100}%` : '0%' }} />
          </div>
          <div className="completionList compactCompletionList">
            {completionItems.map(([moduleId, item]) => (
              <div className={item.ready ? 'complete' : 'incomplete'} key={moduleId}>
                <span>{item.ready ? '✓' : '○'}</span>
                <div>
                  <strong>{item.label}</strong>
                  <small>{item.ready ? 'Inputs present' : `Missing: ${item.missing_fields.join(', ')}`}</small>
                </div>
              </div>
            ))}
          </div>
          <p>Completion measures required inputs only. It is not a country-fit score.</p>
        </section>

        <section className="myFitCard keyActionsCard">
          <div className="myFitCardHeader">
            <h3>Key gaps and actions</h3>
            <span>{gaps.length ? `${gaps.length} open` : 'Ready'}</span>
          </div>
          <div className="keyActionList">
            {gaps.map(([moduleId, item], index) => (
              <article key={moduleId}>
                <span className="keyActionIndex">{index + 1}</span>
                <div>
                  <strong>{item.label} incomplete</strong>
                  <span>Add: {item.missing_fields.join(', ')}</span>
                  <small>Required for {gapPurpose[moduleId] ?? 'personal-fit evidence'}.</small>
                  <em>{gapDecision[moduleId] ?? 'Unlocks personal-fit analysis'}</em>
                </div>
                <button type="button" onClick={() => setEditMode(true)}>Add</button>
              </article>
            ))}
            {!gaps.length && (
              <article className="actionComplete">
                <div>
                  <strong>Core inputs complete</strong>
                  <span>Review evidence quality and remaining country-specific blockers below.</span>
                </div>
              </article>
            )}
          </div>
        </section>
      </div>

      {editMode && (
        <section className="profileEditorCard myFitEditor" aria-label="Profile inputs">
          <div className="profileSectionHeading">
            <div><span>EDIT PROFILE</span><h3>Inputs used for personal-fit analysis</h3></div>
          </div>

          <div className="profileFieldGroup">
            <h4>Personal</h4>
            <div className="profileGrid profileGridPersonal">
              <label><span>Age</span><input type="number" min={16} max={100} value={profile.age ?? ''} onChange={(event) => setProfile({ ...profile, age: event.target.value ? Number(event.target.value) : null })} /></label>
              <label><span>Current country (ISO3)</span><input maxLength={3} value={profile.current_country ?? ''} placeholder="e.g. ESP" onChange={(event) => setProfile({ ...profile, current_country: event.target.value })} /></label>
              <label><span>Citizenships</span><input value={citizenshipsText} placeholder="e.g. ESP, IRL" onChange={(event) => setCitizenshipsText(event.target.value)} /></label>
            </div>
          </div>

          <div className="profileFieldGroup">
            <h4>Career</h4>
            <div className="profileGrid profileGridCareer">
              <label><span>Profession</span><input value={profile.profession ?? ''} placeholder="e.g. Systems engineer" onChange={(event) => setProfile({ ...profile, profession: event.target.value || null })} /></label>
              <label><span>Skills</span><input value={skillsText} placeholder="e.g. Windows, Azure, Python, SQL" onChange={(event) => setSkillsText(event.target.value)} /></label>
            </div>
          </div>

          <div className="profileFieldGroup">
            <h4>Languages</h4>
            <div className="profileGrid profileGridLanguages">
              <label><span>Languages · optional CEFR</span><input value={languagesText} placeholder="e.g. Spanish:C2, English:B2" onChange={(event) => setLanguagesText(event.target.value)} /></label>
              <label>
                <span>Language study hours / week</span>
                <input
                  type="number"
                  min={1}
                  max={80}
                  value={studyHours ?? ''}
                  onChange={(event) => {
                    const preferences = { ...profile.preferences }
                    if (event.target.value) preferences.language_study_hours_per_week = Number(event.target.value)
                    else delete preferences.language_study_hours_per_week
                    setProfile({ ...profile, preferences })
                  }}
                />
              </label>
            </div>
          </div>

          <div className="profileFieldGroup">
            <h4>Financial / household</h4>
            <div className="profileGrid profileGridFinancial">
              <label><span>Household size</span><small className="profileFieldNote">Stored for future household-budget modelling; not used in current FinancialFit.</small><input type="number" min={1} max={20} value={profile.household_size} onChange={(event) => setProfile({ ...profile, household_size: Number(event.target.value) || 1 })} /></label>
              <label><span>Monthly net income</span><input type="number" min={0} value={profile.monthly_net_income ?? ''} onChange={(event) => setProfile({ ...profile, monthly_net_income: event.target.value ? Number(event.target.value) : null })} /></label>
              <label><span>Liquid savings</span><small className="profileFieldNote">Stored for future transition-cost/runway modelling; not used in current FinancialFit.</small><input type="number" min={0} value={profile.liquid_savings ?? ''} onChange={(event) => setProfile({ ...profile, liquid_savings: event.target.value ? Number(event.target.value) : null })} /></label>
              <label className="profileCheckbox"><input type="checkbox" checked={profile.remote_work} onChange={(event) => setProfile({ ...profile, remote_work: event.target.checked })} /><span>Remote work is viable</span></label>
            </div>
          </div>

          <div className="profileSaveRow">
            <button type="button" onClick={save} disabled={status === 'saving'}>{status === 'saving' ? 'Saving…' : 'Save profile'}</button>
          </div>
        </section>
      )}

      <div className="myFitSecondGrid">
        <section className="myFitCard prioritiesCard">
          <div className="myFitCardHeader">
            <h3>Your priorities</h3>
            <span>{selectedPriorityCount} selected · used only when explicit</span>
          </div>
          <p>Select what matters most to you. These preferences are stored locally; they do not alter objective country evidence.</p>
          <div className="priorityChipGrid">
            {priorityOptions.map((item) => {
              const active = profile.preferences[`priority_${item.key}`] === true
              return (
                <button
                  type="button"
                  className={active ? 'active' : ''}
                  key={item.key}
                  aria-pressed={active}
                  onClick={() => togglePriority(item.key)}
                >
                  <span className="priorityIcon">{item.icon}</span>
                  <span className="priorityCopy">
                    <strong>{item.label}</strong>
                    <small>{item.description}</small>
                  </span>
                  <span className="priorityState">{active ? 'Selected' : 'Off'}</span>
                </button>
              )
            })}
          </div>
        </section>

        <section className="myFitCard decisionWeightsCard" aria-label="Decision weights">
          <div className="myFitCardHeader">
            <h3>Decision weights</h3>
            <span>{selectedDecisionWeightCount}/10 explicit</span>
          </div>
          <p>
            Optional P2 weights for personalized comparison. Blank means no personal weight is set;
            0 excludes a dimension; 5 gives the highest relative priority. Objective evidence is unchanged.
          </p>
          <div className="decisionWeightGrid">
            {DECISION_WEIGHT_DIMENSIONS.map(([dimension, label]) => {
              const key = `decision_weight_${dimension}`
              const raw = profile.preferences[key]
              const value = typeof raw === 'number' ? String(raw) : ''
              return (
                <label key={dimension}>
                  <span>{label}</span>
                  <select
                    aria-label={`${label} decision weight`}
                    value={value}
                    onChange={(event) => {
                      const preferences = { ...profile.preferences }
                      if (event.target.value === '') delete preferences[key]
                      else preferences[key] = Number(event.target.value)
                      setProfile({ ...profile, preferences })
                    }}
                  >
                    <option value="">Not set</option>
                    <option value="0">0 · exclude</option>
                    <option value="1">1 · low</option>
                    <option value="2">2</option>
                    <option value="3">3 · medium</option>
                    <option value="4">4</option>
                    <option value="5">5 · highest</option>
                  </select>
                </label>
              )
            })}
          </div>
          <small>
            Save profile to persist these weights. AUGUR normalizes only interpretable indicators and deduplicates semantic constructs before weighting.
          </small>
        </section>

        <section className="myFitCard profileEvidenceCard" aria-label="Personal-fit evidence">
          <div className="myFitCardHeader">
            <h3>Profile evidence</h3>
            <span>{targetCountry}</span>
          </div>
          <p>What evidence is available for the current personal-fit modules.</p>
          <div className="evidenceStatusGrid">
            {evidenceItems.map((item) => (
              <article className={`evidenceStatusCard ${item.state}`} key={item.id}>
                <span className="evidenceStateMark">{item.state === 'complete' ? '●' : item.state === 'partial' ? '◐' : '○'}</span>
                <strong>{item.label.replace('Fit', '')}</strong>
                <span>{item.state}</span>
                <small>{item.detail}</small>
                <div className="evidenceConstraint">
                  <span>Current constraint</span>
                  <strong>{item.constraint}</strong>
                </div>
                <div className="evidenceNextAction">
                  <span>Next action</span>
                  <strong>
                    {readiness?.modules?.[item.readinessKey]?.ready
                      ? 'Core inputs ready'
                      : readiness?.modules?.[item.readinessKey]?.missing_fields?.length
                      ? `Add ${readiness.modules[item.readinessKey].missing_fields.join(', ')}`
                      : item.state === 'partial'
                      ? 'Review remaining evidence blockers'
                      : 'Review module evidence'}
                  </strong>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>

      <details className="myFitDetails">
        <summary>Detailed fit evidence and TTV</summary>
        <div className="fitOutputGrid">
          <article className="fitOutputCard">
            <div className="fitOutputHeader"><span>LEGAL</span><strong>{legalFit?.status?.replaceAll('_', ' ') ?? 'loading'}</strong></div>
            <dl>
              <div><dt>Framework</dt><dd>{legalFit?.framework?.replaceAll('_', ' ') ?? 'Not conclusive'}</dd></div>
              <div><dt>Work permit</dt><dd>{legalFit?.work_permit_required === false ? 'Not required under identified framework' : 'Not established'}</dd></div>
            </dl>
          </article>
          <article className="fitOutputCard">
            <div className="fitOutputHeader"><span>LANGUAGE</span><strong>{languageFit?.status?.replaceAll('_', ' ') ?? 'loading'}</strong></div>
            <dl>
              <div><dt>Targets</dt><dd>{languageFit?.target_languages?.join(' · ') || 'Unavailable'}</dd></div>
              <div><dt>Work-ready heuristic</dt><dd>{languageFit?.work_ready ? 'Met' : 'Not met / incomplete'}</dd></div>
            </dl>
          </article>
          <article className="fitOutputCard">
            <div className="fitOutputHeader"><span>CAREER</span><strong>{careerFit?.status?.replaceAll('_', ' ') ?? 'loading'}</strong></div>
            <dl>
              <div><dt>Market signal</dt><dd>{careerFit?.market_signal?.replaceAll('_', ' ') ?? 'Unavailable'}</dd></div>
              <div><dt>Skill coverage</dt><dd>{careerFit?.skill_match.coverage == null ? 'Unavailable' : `${Math.round(careerFit.skill_match.coverage * 100)}%`}</dd></div>
            </dl>
          </article>
          <article className="fitOutputCard">
            <div className="fitOutputHeader"><span>FINANCIAL</span><strong>{financialFit?.status?.replaceAll('_', ' ') ?? 'loading'}</strong></div>
            <dl>
              <div><dt>Evidence</dt><dd>{financialFit?.evidence_state?.replaceAll('_', ' ') ?? 'Unavailable'}</dd></div>
              <div><dt>Blockers</dt><dd>{financialFit?.blockers?.length ? financialFit.blockers.join(' · ').replaceAll('_', ' ') : 'None returned'}</dd></div>
            </dl>
          </article>
        </div>
        <section className="ttvCompact" role="region" aria-label="TTV readiness">
          <div>
            <strong>TTV</strong>
            <span>{ttv?.ready_for_time_estimate ? 'Estimate available' : ttv?.dependency_ready ? 'Dependencies ready · temporal model incomplete' : 'Blocked by incomplete dependencies'}</span>
          </div>
          {!ttv?.dependency_ready && (
            <div className="ttvCompactEvidence">
              <strong>Blocked by</strong>
              <span>{ttv?.blocked_by?.length ? ttv.blocked_by.join(' · ').replaceAll('_', ' ') : 'Waiting for evidence'}</span>
            </div>
          )}
          {ttv?.candidate_time_range && (
            <div className="ttvCompactEvidence">
              <strong>Temporal evidence · candidate only</strong>
              <span>
                {ttv.candidate_time_range.weeks_min}–{ttv.candidate_time_range.weeks_max} weeks · critical path: preparation parallel → employment → financial · not an AUGUR estimate
              </span>
            </div>
          )}
          {ttv?.temporal_evidence?.stages?.language && (
            <div className="ttvCompactEvidence">
              <strong>Language planning evidence</strong>
              <span>
                {ttv.temporal_evidence.stages.language.guided_hours_min != null && ttv.temporal_evidence.stages.language.guided_hours_max != null
                  ? `Language: ${ttv.temporal_evidence.stages.language.guided_hours_min}–${ttv.temporal_evidence.stages.language.guided_hours_max} guided hours${ttv.temporal_evidence.stages.language.weekly_study_hours == null ? ' · add study hours/week for calendar conversion' : ''}`
                  : 'Language timing evidence unavailable'}
              </span>
            </div>
          )}
          {ttvObservation ? (
            <div className="ttvCalibrationCard active" aria-label="TTV calibration observation">
              <div>
                <strong>TTV v1 calibration observation active</strong>
                <span>
                  Started {new Date(ttvObservation.started_at).toLocaleDateString()} · candidate {ttvObservation.candidate_weeks_min}–{ttvObservation.candidate_weeks_max} weeks
                </span>
              </div>
              <p>
                Local opt-in development evidence only. When you have a documented B2-or-better result, record the outcome here; this does not turn the candidate range into an AUGUR estimate.
              </p>
              <div className="ttvCalibrationActions">
                <button
                  type="button"
                  onClick={() => void completeTtvObservation()}
                  disabled={ttvObservationStatus === 'working'}
                >
                  Record B2 outcome now
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => void cancelTtvObservation()}
                  disabled={ttvObservationStatus === 'working'}
                >
                  Cancel observation
                </button>
              </div>
            </div>
          ) : ttvCalibrationEligible ? (
            <div className="ttvCalibrationCard" aria-label="TTV calibration opt in">
              <div>
                <strong>Help validate TTV v1</strong>
                <span>
                  Eligible bounded case · {ttv?.candidate_time_range?.weeks_min}–{ttv?.candidate_time_range?.weeks_max} week candidate range
                </span>
              </div>
              <p>
                Opt in to save this baseline locally as development calibration evidence. AUGUR stores the candidate range and start date; no holdout or validation claim is created.
              </p>
              <button
                type="button"
                onClick={() => void startTtvObservation()}
                disabled={ttvObservationStatus === 'working' || ttvObservationStatus === 'loading'}
              >
                Start calibration observation
              </button>
            </div>
          ) : null}
          {ttvObservationStatus === 'error' && (
            <div className="ttvCalibrationError">
              Calibration observation action failed. TTV analysis remains unchanged.
            </div>
          )}
          <div className="ttvExchangeCard" aria-label="TTV calibration data portability">
            <div>
              <strong>Calibration data portability</strong>
              <span>Development cases only · profile and personal history excluded</span>
            </div>
            {ttvCalibrationStatus && (
              <div className="ttvCalibrationDiagnostics" aria-label="TTV calibration diagnostics">
                <article>
                  <span>Development cases</span>
                  <strong>{ttvCalibrationStatus.development_case_count}</strong>
                </article>
                <article>
                  <span>Interval coverage</span>
                  <strong>
                    {ttvCalibrationStatus.interval_coverage_pct == null
                      ? '—'
                      : `${ttvCalibrationStatus.interval_coverage_pct.toFixed(1)}%`}
                  </strong>
                </article>
                <article>
                  <span>Mean interval width</span>
                  <strong>
                    {ttvCalibrationStatus.mean_interval_width_weeks == null
                      ? '—'
                      : `${ttvCalibrationStatus.mean_interval_width_weeks.toFixed(1)} wk`}
                  </strong>
                </article>
                <article>
                  <span>CEFR starts</span>
                  <strong>
                    {ttvCalibrationStatus.context_summary.current_cefr_levels.length
                      ? ttvCalibrationStatus.context_summary.current_cefr_levels.join(' · ')
                      : '—'}
                  </strong>
                </article>
              </div>
            )}
            {ttvCalibrationStatus?.context_summary.weekly_study_hours.length ? (
              <small>
                Study-intensity cohorts: {ttvCalibrationStatus.context_summary.weekly_study_hours.join(' · ')} h/week
              </small>
            ) : null}
            <div className="ttvCalibrationActions">
              <button
                type="button"
                className="secondary"
                onClick={() => void exportTtvDevelopmentData()}
                disabled={ttvExchangeStatus === 'working'}
              >
                Export anonymous development cases
              </button>
              <label className="ttvImportButton">
                Import anonymous development cases
                <input
                  type="file"
                  accept="application/json,.json"
                  disabled={ttvExchangeStatus === 'working'}
                  onChange={(event) => {
                    const file = event.target.files?.[0]
                    if (file) void importTtvDevelopmentData(file)
                    event.currentTarget.value = ''
                  }}
                />
              </label>
            </div>
            {ttvExchangeStatus === 'saved' && <small>Anonymous development package exported.</small>}
            {ttvExchangeStatus === 'imported' && <small>Development package imported locally.</small>}
            {ttvExchangeStatus === 'error' && <small className="error">Calibration exchange failed; existing cases were not reclassified.</small>}
          </div>
        </section>
      </details>
    </section>
  )
}

