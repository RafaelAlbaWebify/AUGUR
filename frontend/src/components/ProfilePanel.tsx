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
  }
  market_signal: string | null
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
  evidence_complete: boolean
  profile_skill_coverage_complete?: boolean
  market_signal_supports_viability?: boolean
  viability_evidence_ready?: boolean
  rule_version: string
  source: null | {
    label: string
    url: string
  }
  notes: string[]
}

type FinancialFitResponse = {
  target_country_iso3: string
  status: string
  reason: string | null
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
    unavailable_stages: string[]
    candidate_range: null | {
      weeks_min: number
      weeks_max: number
      composition: string
    }
    stages: Record<string, {
      status: string
      weeks_min: number | null
      weeks_max: number | null
      reason: string
      guided_hours_min?: number | null
      guided_hours_max?: number | null
      weekly_study_hours?: number | null
    }>
  }
  candidate_time_range?: null | {
    weeks_min: number
    weeks_max: number
    composition: string
  }
  estimate_status?: string
  ready_for_time_estimate: boolean
  time_estimate: null
  notes: string[]
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
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null)
  const [financialFit, setFinancialFit] = useState<FinancialFitResponse | null>(null)
  const [legalFit, setLegalFit] = useState<LegalFitResponse | null>(null)
  const [languageFit, setLanguageFit] = useState<LanguageFitResponse | null>(null)
  const [careerFit, setCareerFit] = useState<CareerFitResponse | null>(null)
  const [ttv, setTtv] = useState<TTVResponse | null>(null)
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
    void refreshTargetFits()
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
      label: 'LegalFit',
      state: !legalFit || legalFit.status === 'insufficient_profile'
        ? 'incomplete'
        : legalFit.status === 'country_specific_rules_required'
        ? 'partial'
        : 'complete',
      detail: legalFit?.status?.replaceAll('_', ' ') ?? 'loading',
    },
    {
      id: 'language',
      label: 'LanguageFit',
      state: !languageFit || languageFit.status === 'target_language_missing'
        ? 'incomplete'
        : 'complete',
      detail: languageFit?.status?.replaceAll('_', ' ') ?? 'loading',
    },
    {
      id: 'career',
      label: 'CareerFit',
      state: !careerFit || careerFit.status === 'profession_missing'
        ? 'incomplete'
        : careerFit.evidence_complete
        ? 'complete'
        : 'partial',
      detail: careerFit?.status?.replaceAll('_', ' ') ?? 'loading',
    },
    {
      id: 'financial',
      label: 'FinancialFit',
      state: !financialFit || !financialFit.portable_income_analysis
        ? 'incomplete'
        : 'complete',
      detail: financialFit?.status?.replaceAll('_', ' ') ?? 'loading',
    },
  ]

  return (
    <section className="profilePageV2" aria-label="Personal profile">
      <header className="profilePageHeader">
        <div>
          <span>PROFILE</span>
          <h2>Your information</h2>
          <p>Stored locally · never changes country facts</p>
        </div>
        <div className="profileTargetBadge">
          <span>Evaluating</span>
          <strong>{targetCountry}</strong>
        </div>
      </header>

      <div className="profileTopGrid">
        <section className="profileEditorCard" aria-label="Profile inputs">
          <div className="profileSectionHeading">
            <div>
              <span>YOUR PROFILE</span>
              <h3>Inputs used for personal-fit analysis</h3>
            </div>
            <span>{status === 'saved' ? 'Saved locally' : status === 'saving' ? 'Saving…' : status === 'error' ? 'Save unavailable' : 'Local draft'}</span>
          </div>

          <div className="profileFieldGroup">
            <h4>Personal</h4>
            <div className="profileGrid">
              <label>
                <span>Age</span>
                <input
                  type="number"
                  min={16}
                  max={100}
                  value={profile.age ?? ''}
                  onChange={(event) => setProfile({ ...profile, age: event.target.value ? Number(event.target.value) : null })}
                />
              </label>
              <label>
                <span>Current country (ISO3)</span>
                <input
                  maxLength={3}
                  value={profile.current_country ?? ''}
                  placeholder="ESP"
                  onChange={(event) => setProfile({ ...profile, current_country: event.target.value })}
                />
              </label>
              <label className="profileWide">
                <span>Citizenships</span>
                <input value={citizenshipsText} placeholder="ESP, IRL" onChange={(event) => setCitizenshipsText(event.target.value)} />
              </label>
            </div>
          </div>

          <div className="profileFieldGroup">
            <h4>Career</h4>
            <div className="profileGrid">
              <label>
                <span>Profession</span>
                <input
                  value={profile.profession ?? ''}
                  placeholder="Systems engineer"
                  onChange={(event) => setProfile({ ...profile, profession: event.target.value || null })}
                />
              </label>
              <label className="profileWide">
                <span>Skills</span>
                <input value={skillsText} placeholder="Windows, Azure, Python, SQL" onChange={(event) => setSkillsText(event.target.value)} />
              </label>
            </div>
          </div>

          <div className="profileFieldGroup">
            <h4>Languages</h4>
            <div className="profileGrid">
              <label className="profileWide">
                <span>Languages · optional CEFR</span>
                <input value={languagesText} placeholder="Spanish:C2, English:B2" onChange={(event) => setLanguagesText(event.target.value)} />
              </label>
              <label>
                <span>Language study hours / week · TTV</span>
                <input
                  type="number"
                  min={1}
                  max={80}
                  step={1}
                  value={
                    typeof profile.preferences.language_study_hours_per_week === 'number'
                      ? profile.preferences.language_study_hours_per_week
                      : ''
                  }
                  placeholder="e.g. 10"
                  onChange={(event) => {
                    const preferences = { ...profile.preferences }
                    if (event.target.value) {
                      preferences.language_study_hours_per_week = Number(event.target.value)
                    } else {
                      delete preferences.language_study_hours_per_week
                    }
                    setProfile({ ...profile, preferences })
                  }}
                />
              </label>
            </div>
          </div>

          <div className="profileFieldGroup">
            <h4>Financial / household</h4>
            <div className="profileGrid">
              <label>
                <span>Household size</span>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={profile.household_size}
                  onChange={(event) => setProfile({ ...profile, household_size: Number(event.target.value) || 1 })}
                />
              </label>
              <label>
                <span>Monthly net income</span>
                <input
                  type="number"
                  min={0}
                  value={profile.monthly_net_income ?? ''}
                  onChange={(event) => setProfile({ ...profile, monthly_net_income: event.target.value ? Number(event.target.value) : null })}
                />
              </label>
              <label>
                <span>Liquid savings</span>
                <input
                  type="number"
                  min={0}
                  value={profile.liquid_savings ?? ''}
                  onChange={(event) => setProfile({ ...profile, liquid_savings: event.target.value ? Number(event.target.value) : null })}
                />
              </label>
              <label className="profileCheckbox">
                <input
                  type="checkbox"
                  checked={profile.remote_work}
                  onChange={(event) => setProfile({ ...profile, remote_work: event.target.checked })}
                />
                <span>Remote work is viable</span>
              </label>
            </div>
          </div>

          <div className="profileSaveRow">
            <button type="button" onClick={save} disabled={status === 'saving'}>
              {status === 'saving' ? 'Saving…' : 'Save profile'}
            </button>
          </div>
        </section>

        <aside className="profileCompletionCard" role="region" aria-label="Profile completion">
          <div className="profileSectionHeading">
            <div>
              <span>PROFILE COMPLETION</span>
              <h3>{readiness ? `${readiness.ready_module_count} / ${readiness.module_count} input sets ready` : 'Checking inputs…'}</h3>
            </div>
          </div>

          <div className="completionMeter" aria-hidden="true">
            <i style={{ width: readiness && readiness.module_count ? `${(readiness.ready_module_count / readiness.module_count) * 100}%` : '0%' }} />
          </div>

          <div className="completionList">
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

          <p>Completion only confirms that required profile inputs exist. It is not a country-fit score.</p>
        </aside>
      </div>

      <section className="profileEvidenceSection" aria-label="Personal-fit evidence">
        <div className="profileSectionHeading">
          <div>
            <span>PERSONAL-FIT EVIDENCE · {targetCountry}</span>
            <h3>Evidence availability</h3>
          </div>
          <small>complete · partial · incomplete</small>
        </div>

        <div className="evidenceStatusGrid">
          {evidenceItems.map((item) => (
            <article className={`evidenceStatusCard ${item.state}`} key={item.id}>
              <span className="evidenceStateMark">{item.state === 'complete' ? '●' : item.state === 'partial' ? '◐' : '○'}</span>
              <strong>{item.label}</strong>
              <span>{item.state}</span>
              <small>{item.detail}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="fitOutputsSection" aria-label="Fit outputs">
        <div className="profileSectionHeading">
          <div>
            <span>FIT OUTPUTS · {targetCountry}</span>
            <h3>What AUGUR can currently conclude</h3>
          </div>
        </div>

        <div className="fitOutputGrid">
          <article className="fitOutputCard">
            <div className="fitOutputHeader"><span>LEGAL</span><strong>{legalFit?.status?.replaceAll('_', ' ') ?? 'loading'}</strong></div>
            <dl>
              <div><dt>Result</dt><dd>{legalFit?.status === 'eu_free_movement_framework' ? 'EU free-movement framework' : legalFit?.status === 'domestic' ? 'Domestic case' : 'Not yet conclusive'}</dd></div>
              <div><dt>Why</dt><dd>{legalFit?.work_permit_required === false ? 'Work permit not required under the identified framework.' : 'Profile or country-specific rules still limit the conclusion.'}</dd></div>
              <div><dt>Limitation</dt><dd>Long-stay conditions and national registration formalities may still apply.</dd></div>
            </dl>
          </article>

          <article className="fitOutputCard">
            <div className="fitOutputHeader"><span>LANGUAGE</span><strong>{languageFit?.status?.replaceAll('_', ' ') ?? 'loading'}</strong></div>
            <dl>
              <div><dt>Result</dt><dd>{languageFit ? (languageFit.work_ready ? `Meets AUGUR ${languageFit.work_ready_threshold}+ heuristic` : `Below AUGUR ${languageFit.work_ready_threshold} heuristic`) : 'Loading evidence'}</dd></div>
              <div><dt>Why</dt><dd>{languageFit?.target_languages?.length ? `Target: ${languageFit.target_languages.join(' · ')}` : 'Target-language evidence unavailable.'}</dd></div>
              <div>
                <dt>Evidence</dt>
                <dd>
                  {languageFit?.occupation_language_evidence?.status === 'occupation_language_evidence_available'
                    ? `ESCO ${languageFit.occupation_language_evidence.dataset_version ?? ''} · ${languageFit.occupation_language_evidence.occupation_label} · ${languageFit.occupation_language_evidence.essential_skill_count} essential / ${languageFit.occupation_language_evidence.optional_skill_count} optional language skills`
                    : languageFit?.occupation_language_evidence
                    ? `ESCO occupation-language evidence: ${languageFit.occupation_language_evidence.status.replaceAll('_', ' ')}`
                    : 'ESCO occupation-language evidence not evaluated.'}
                </dd>
              </div>
              <div><dt>Limitation</dt><dd>B2 is an AUGUR employment heuristic, not a legal requirement; ESCO relations do not encode CEFR level.</dd></div>
            </dl>
          </article>

          <article className="fitOutputCard">
            <div className="fitOutputHeader"><span>CAREER</span><strong>{careerFit?.status?.replaceAll('_', ' ') ?? 'loading'}</strong></div>
            <dl>
              <div><dt>Result</dt><dd>{careerFit?.market_signal?.replaceAll('_', ' ') ?? 'No conclusive market signal'}</dd></div>
              <div>
                <dt>Why</dt>
                <dd>
                  {careerFit?.occupation_match?.selected
                    ? `ESCO: ${careerFit.occupation_match.selected.preferred_label} · ${Math.round(careerFit.occupation_match.selected.match_score * 100)}% label match`
                    : careerFit?.occupation.occupation_group
                    ? `Occupation group: ${careerFit.occupation.occupation_group.replaceAll('_', ' ')} · no confident ESCO occupation match`
                    : 'Occupation not yet mapped.'}
                </dd>
              </div>
              <div>
                <dt>Evidence</dt>
                <dd>
                  {careerFit?.skill_match.dataset_mode
                    ? `ESCO ${careerFit.skill_match.dataset_mode} · ${careerFit.skill_match.coverage == null ? 'coverage unavailable' : `${Math.round(careerFit.skill_match.coverage * 100)}% essential-skill coverage`}`
                    : 'ESCO skill evidence not evaluated.'}
                </dd>
              </div>
              <div>
                <dt>TTV gate</dt>
                <dd>
                  {careerFit?.viability_evidence_ready
                    ? 'Supportive shortage signal + complete declared essential-skill coverage'
                    : careerFit?.evidence_complete
                    ? `Blocked · ${careerFit.profile_skill_coverage_complete ? 'essential skills covered' : 'essential skill coverage incomplete'} · ${careerFit.market_signal_supports_viability ? 'supportive market signal' : 'market signal not supportive'}`
                    : 'Blocked · career evidence incomplete'}
                </dd>
              </div>
              <div><dt>Limitation</dt><dd>{careerFit?.evidence_complete ? 'AUGUR only treats declared essential-skill coverage as present; undeclared skills are not inferred.' : 'Evidence remains partial until a confident ESCO occupation match and full skill dataset are available.'}</dd></div>
            </dl>
          </article>

          <article className="fitOutputCard">
            <div className="fitOutputHeader"><span>FINANCIAL</span><strong>{financialFit?.status?.replaceAll('_', ' ') ?? 'loading'}</strong></div>
            <dl>
              <div>
                <dt>Result</dt>
                <dd>
                  {financialFit?.portable_income_analysis
                    ? `${financialFit.portable_income_analysis.purchasing_power_change_pct > 0 ? '+' : ''}${financialFit.portable_income_analysis.purchasing_power_change_pct.toFixed(1)}% purchasing-power change`
                    : financialFit?.local_income_reference
                    ? `€${new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(financialFit.local_income_reference.gross_monthly_mean_eur)} gross/month reference`
                    : 'Not yet conclusive'}
                </dd>
              </div>
              <div>
                <dt>Why</dt>
                <dd>
                  {financialFit?.portable_income_analysis
                    ? `Relative cost factor ×${financialFit.portable_income_analysis.relative_cost_factor.toFixed(2)}`
                    : financialFit?.local_income_reference
                    ? `Eurostat SES ${financialFit.local_income_reference.period} · ${financialFit.local_income_reference.occupation_label} · ${financialFit.local_income_reference.ses_isco_major_group}`
                    : 'Portable or local-income evidence unavailable.'}
                </dd>
              </div>
              <div>
                <dt>Limitation</dt>
                <dd>
                  {financialFit?.local_income_reference
                    ? financialFit.national_net_earnings_reference
                      ? `Gross occupation reference + €${new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(financialFit.national_net_earnings_reference.monthly_net_equivalent_eur)} net/month national average-worker benchmark; occupation-specific net pay is not inferred.`
                      : 'Structural mean gross earnings only; occupation-specific net pay, taxes, location and household budget are not yet modelled.'
                    : 'Local-income and household assumptions may require additional evidence.'}
                </dd>
              </div>
            </dl>
          </article>
        </div>
      </section>

      <section className="ttvReadinessSection" aria-label="TTV readiness">
        <div className="profileSectionHeading">
          <div>
            <span>TTV READINESS · {targetCountry}</span>
            <h3>Dependency path</h3>
          </div>
          <strong>
            {ttv?.ready_for_time_estimate
              ? 'Estimate available'
              : ttv?.dependency_ready
              ? 'Dependencies ready · temporal model missing'
              : 'Time estimate unavailable'}
          </strong>
        </div>

        <div className="ttvDependencyPath">
          {(ttv?.stage_order ?? ['legal_fit', 'language_fit', 'career_fit', 'financial_fit']).map((stageId, index, stages) => {
            const stage = ttv?.stages?.[stageId]
            return (
              <div className="ttvStageWrap" key={stageId}>
                <div className={`ttvStage ${stage?.ready ? 'ready' : 'blocked'}`}>
                  <span>{stage?.ready ? '✓' : '○'}</span>
                  <strong>{stageId.replace('_fit', 'Fit').replace('_', ' ')}</strong>
                  <small>{stage?.evidence_state?.replaceAll('_', ' ') ?? 'checking'}</small>
                </div>
                {index < stages.length - 1 && <span className="ttvConnector">→</span>}
              </div>
            )
          })}
          <span className="ttvConnector">→</span>
          <div className={`ttvStage final ${ttv?.ready_for_time_estimate ? 'ready' : 'blocked'}`}>
            <span>{ttv?.ready_for_time_estimate ? '✓' : '○'}</span>
            <strong>TTV</strong>
            <small>{ttv?.ready_for_time_estimate ? 'ready' : 'blocked'}</small>
          </div>
        </div>

        {!ttv?.ready_for_time_estimate && (
          <div className="ttvBlockedReason">
            <strong>{ttv?.dependency_ready ? 'Timing model' : 'Blocked by'}</strong>
            <span>
              {ttv?.dependency_ready
                ? `Temporal evidence: ${ttv.temporal_evidence_state?.replaceAll('_', ' ') ?? 'not implemented'}`
                : ttv?.blocker_details?.length
                ? ttv.blocker_details
                    .map((item) => `${item.stage_id.replaceAll('_', ' ')} · ${(item.reason ?? item.status).replaceAll('_', ' ')} · ${item.evidence_state.replaceAll('_', ' ')}`)
                    .join(' | ')
                : ttv?.blocked_by?.length
                ? ttv.blocked_by.map((item) => item.replaceAll('_', ' ')).join(' · ')
                : 'Waiting for evidence'}
            </span>
          </div>
        )}

        {ttv?.temporal_evidence && (
          <div className="ttvTemporalEvidence">
            <strong>Temporal evidence · candidate only</strong>
            {ttv.candidate_time_range ? (
              <span>
                {ttv.candidate_time_range.weeks_min}–{ttv.candidate_time_range.weeks_max} weeks · parallel max · not an AUGUR estimate
              </span>
            ) : (
              <span>
                Missing calendar evidence: {ttv.temporal_evidence.unavailable_stages.join(' · ') || 'none'}
              </span>
            )}
            {ttv.temporal_evidence.stages.language?.guided_hours_min != null && (
              <small>
                Language: {ttv.temporal_evidence.stages.language.guided_hours_min}–{ttv.temporal_evidence.stages.language.guided_hours_max} guided hours
                {ttv.temporal_evidence.stages.language.weekly_study_hours
                  ? ` · ${ttv.temporal_evidence.stages.language.weekly_study_hours} h/week`
                  : ' · add study hours/week for calendar conversion'}
              </small>
            )}
          </div>
        )}

        <p>
          Time-to-viability requires both viable dependencies and a validated temporal evidence model.
          Dependency readiness alone never creates a duration.
        </p>
      </section>
    </section>
  )
}
