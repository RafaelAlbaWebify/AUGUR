import { useEffect, useMemo, useState } from 'react'

type SkillsLanguagesPageProps = {
  apiBase: string
  targetCountry: string
  countryName: string
}

type Profile = {
  profession?: string | null
  skills?: string[]
  languages?: Array<{ language?: string; name?: string; cefr?: string; level?: string }>
}

type CareerFit = {
  status?: string
  market_signal?: string | null
  market_signal_scope?: string
  market_signal_isco?: string | null
  occupation_match?: {
    selected?: {
      preferred_label?: string
      match_score?: number
      isco_group?: string
      code?: string
    } | null
  }
  eu27_oja_imbalance_evidence?: {
    status?: string
    isco08?: string
    occupation_label?: string
    score?: number
    release_version?: string
    geographic_scope?: string
    role?: string
  } | null
  occupation_outlook_evidence?: {
    status?: string
    source_id?: string
    dataset_id?: string
    release_version?: string
    isco08?: string
    granularity?: string
    occupation_label?: string
    horizons?: Array<{
      period?: number
      employment_level_thousands?: number | null
      employment_growth_pct?: number | null
    }>
    role?: string
  } | null
  occupation_trend_evidence?: {
    status?: string
    evidence_type?: string
    latest_period?: number
    latest_growth_pct?: number
    direction?: string
    role?: string
  } | null
  skill_demand_trend_evidence?: {
    status?: string
    source_id?: string
    dataset_id?: string
    access_path?: string
    reproducible_public_ingestion?: boolean
    role?: string
  } | null
  language_oja_requirements_evidence?: {
    status?: string
    source_id?: string
    dataset_id?: string
    access_path?: string
    reproducible_public_ingestion?: boolean
    role?: string
  } | null
  vacancy_demand_evidence?: {
    status?: string
    vacancy_rate_pct?: number
    period?: string
    source_id?: string
    granularity?: string
    isco_major?: string
    isco_3digit?: string
    dataset_id?: string
    supported_countries?: string[]
  } | null
  skill_match?: {
    dataset_mode?: string | null
    dataset_version?: string | null
    occupation_label?: string | null
    matched_skills?: Array<string | { label?: string; skill?: string; name?: string }>
    missing_skills?: Array<string | { label?: string; skill?: string; name?: string }>
    coverage?: number | null
    evidence_complete?: boolean
  }
  source?: {
    label?: string
    evidence_id?: string
    rule_version?: string
    report_year?: number
    conditions_year?: number
    scope?: string
  } | null
}

type LanguageFit = {
  status?: string
  target_languages?: string[]
  matches?: Array<{
    language: string
    declared_cefr?: string | null
    meets_work_ready_heuristic?: boolean
  }>
  work_ready_threshold?: string
  work_ready?: boolean
  occupation_language_evidence?: {
    status?: string
    occupation_label?: string
    essential_skill_count?: number
    optional_skill_count?: number
  } | null
}

function skillLabel(value: string | { label?: string; skill?: string; name?: string }) {
  if (typeof value === 'string') return value
  return value.label ?? value.skill ?? value.name ?? 'Unnamed skill'
}

function languageLevel(profile: Profile | null, language: string) {
  const match = (profile?.languages ?? []).find((item) => {
    const name = item.language ?? item.name
    return name?.toLowerCase() === language.toLowerCase()
  })
  return match?.cefr ?? match?.level ?? 'Not set'
}

export default function SkillsLanguagesPage({
  apiBase,
  targetCountry,
  countryName,
}: SkillsLanguagesPageProps) {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [career, setCareer] = useState<CareerFit | null>(null)
  const [language, setLanguage] = useState<LanguageFit | null>(null)
  const [tab, setTab] = useState<'demand' | 'rising' | 'gaps' | 'portable' | 'languages'>('demand')

  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal

    Promise.all([
      fetch(`${apiBase}/api/profile`, { signal }).then((r) => r.ok ? r.json() : null),
      fetch(`${apiBase}/api/countries/${targetCountry}/career-fit`, { signal }).then((r) => r.ok ? r.json() : null),
      fetch(`${apiBase}/api/countries/${targetCountry}/language-fit`, { signal }).then((r) => r.ok ? r.json() : null),
    ]).then(([profileData, careerData, languageData]) => {
      if (signal.aborted) return
      setProfile(profileData)
      setCareer(careerData)
      setLanguage(languageData)
    }).catch(() => undefined)

    return () => controller.abort()
  }, [apiBase, targetCountry])

  const matched = useMemo(
    () => (career?.skill_match?.matched_skills ?? []).map(skillLabel),
    [career],
  )
  const missing = useMemo(
    () => (career?.skill_match?.missing_skills ?? []).map(skillLabel),
    [career],
  )

  const visibleSkills = tab === 'gaps'
    ? missing
    : tab === 'portable'
    ? [...new Set([...(profile?.skills ?? []), ...matched])].slice(0, 20)
    : tab === 'demand'
    ? [...new Set([...(profile?.skills ?? []), ...matched, ...missing])].slice(0, 20)
    : []

  const demandEvidenceAvailable = career?.vacancy_demand_evidence?.status === 'available'
  const demandCoverageUnavailable = career?.vacancy_demand_evidence?.status === 'source_coverage_unavailable'
  const demandEvidenceLabel = demandEvidenceAvailable
    ? `${career?.vacancy_demand_evidence?.vacancy_rate_pct?.toFixed(1)}% · ${career?.vacancy_demand_evidence?.period}`
    : demandCoverageUnavailable
    ? `Eurostat experimental ISCO-3 source does not cover ${countryName}`
    : 'No verified vacancy context loaded'
  const liveSkillDemandAvailable = false
  const occupationOutlook = career?.occupation_outlook_evidence
  const occupationTrend = career?.occupation_trend_evidence
  const skillDemandTrend = career?.skill_demand_trend_evidence
  const languageOjaRequirements = career?.language_oja_requirements_evidence
  const eu27OjaImbalance = career?.eu27_oja_imbalance_evidence
  const profileReadyForSkills = Boolean(
    (profile?.profession && profile.profession.trim()) ||
    career?.occupation_match?.selected?.preferred_label,
  )
  const hasDeclaredSkills = Boolean(profile?.skills?.length)
  const hasLanguages = Boolean(profile?.languages?.length)
  const profileGaps = [
    !profileReadyForSkills ? 'profession' : null,
    !hasDeclaredSkills ? 'skills' : null,
    !hasLanguages ? 'languages' : null,
  ].filter((item): item is string => Boolean(item))

  return (
    <section className="skillsLanguagesPage" aria-label="Skills and languages">
      <div className="productPageHeader">
        <div>
          <span>6. SKILLS & LANGUAGES</span>
          <h2>Demand, trends and your match</h2>
        </div>
        <p>What to learn, what transfers, and what the evidence can currently support.</p>
      </div>

      <section className="skillsControlBar">
        <label>
          <span>Target occupation</span>
          <strong>{career?.occupation_match?.selected?.preferred_label ?? profile?.profession ?? 'Add profession in Profile'}</strong>
        </label>
        <label>
          <span>Country / region</span>
          <strong>{countryName} · national</strong>
        </label>
        <label>
          <span>Time horizon</span>
          <strong>Current evidence</strong>
        </label>
        <div className="evidenceModeBadge">OFFICIAL / VERIFIED EVIDENCE ONLY</div>
      </section>

      <div className="skillsLanguagesGrid">
        <section className="skillsDemandPanel">
          {!profileReadyForSkills ? (
            <section className="skillsOnboardingState" aria-label="Skills profile onboarding">
              <div className="skillsOnboardingHero">
                <span>PROFILE INPUT REQUIRED</span>
                <h3>Add your profession to unlock occupation-level evidence</h3>
                <p>
                  AUGUR needs a target occupation before it can match ESCO skills, interpret shortage/surplus evidence,
                  or connect future occupational demand. No skill-demand percentages are inferred from an empty profile.
                </p>
              </div>

              <div className="skillsUnlockGrid">
                <article>
                  <span>1</span>
                  <div><strong>Profession</strong><small>Resolves an ESCO / ISCO occupation.</small></div>
                  <b>{profileReadyForSkills ? 'ready' : 'required'}</b>
                </article>
                <article>
                  <span>2</span>
                  <div><strong>Skills</strong><small>Separates matched skills from gaps.</small></div>
                  <b>{hasDeclaredSkills ? 'ready' : 'recommended'}</b>
                </article>
                <article>
                  <span>3</span>
                  <div><strong>Languages</strong><small>Enables CEFR and occupation-language checks.</small></div>
                  <b>{hasLanguages ? 'ready' : 'recommended'}</b>
                </article>
              </div>

              <div className="skillsUnlockEvidence">
                <div>
                  <span>AVAILABLE NOW</span>
                  <strong>Country vacancy context</strong>
                  <small>{demandEvidenceLabel}</small>
                </div>
                <div>
                  <span>UNLOCKS NEXT</span>
                  <strong>ESCO occupation + skill matching</strong>
                  <small>Official taxonomy evidence, not employer-demand frequency.</small>
                </div>
                <div>
                  <span>FUTURE DATA LAYER</span>
                  <strong>Cedefop occupation demand</strong>
                  <small>Public OJA shortage + short-term forecast datasets are the next ingestion target.</small>
                </div>
              </div>

              <p className="skillsOnboardingFooter">
                Missing profile fields: {profileGaps.join(', ') || 'none'} · Edit them in My Fit / Profile.
              </p>
            </section>
          ) : (
            <>
              <section className="skillsDecisionSummary" aria-label="Skills decision summary">
                <article className="nextFocus">
                  <span>NEXT TO LEARN</span>
                  <strong>{missing.length ? `${missing.length} occupation-skill gaps` : 'No ESCO skill gaps identified'}</strong>
                  <p>
                    {missing.length
                      ? missing.slice(0, 3).join(' · ')
                      : 'Current declared/matched skills cover the occupation evidence AUGUR has loaded.'}
                  </p>
                  <small>ESCO occupation relationship · not employer-demand frequency</small>
                </article>

                <article className="portableAssets">
                  <span>PORTABLE ASSETS</span>
                  <strong>{matched.length} matched occupation skills</strong>
                  <p>
                    {matched.length
                      ? matched.slice(0, 3).join(' · ')
                      : 'No matched occupation skills resolved yet.'}
                  </p>
                  <small>Transferability means occupation relevance, not guaranteed hiring demand</small>
                </article>

                <article className="languageLeverage">
                  <span>LANGUAGE READINESS</span>
                  <strong>
                    {(language?.matches ?? []).filter((item) => item.meets_work_ready_heuristic).length}
                    /{(language?.matches ?? []).length || 0} target languages at heuristic
                  </strong>
                  <p>
                    {(language?.matches ?? []).length
                      ? (language?.matches ?? []).map((item) => `${item.language}: ${item.declared_cefr ?? languageLevel(profile, item.language)}`).join(' · ')
                      : 'No target-language evidence resolved.'}
                  </p>
                  <small>AUGUR work-ready heuristic · not a legal requirement</small>
                </article>

                <article className="marketContext">
                  <span>MARKET CONTEXT</span>
                  <strong>{career?.market_signal?.replaceAll('_', ' ') ?? 'Unavailable'}</strong>
                  <p>
                    {demandEvidenceAvailable
                      ? `Vacancy context ${demandEvidenceLabel}`
                      : demandCoverageUnavailable
                      ? demandEvidenceLabel
                      : 'No verified vacancy context loaded.'}
                  </p>
                  <small>Context only · not a skill-demand ranking</small>
                </article>
              </section>

              <div className="segmentedTabs" role="tablist" aria-label="Skills views">
                {[
                  ['demand', 'Skills in demand'],
                  ['rising', 'Rising skills'],
                  ['gaps', 'My gaps'],
                  ['portable', 'Portable skills'],
                  ['languages', 'Job-ad language demand'],
                ].map(([id, label]) => (
                  <button
                    key={id}
                    type="button"
                    className={tab === id ? 'active' : ''}
                    onClick={() => setTab(id as typeof tab)}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {tab === 'rising' ? (
                <div className="evidenceUnavailable">
                  <strong>
                    {occupationTrend?.status === 'available'
                      ? `Occupation outlook: ${occupationTrend.direction?.replaceAll('_', ' ') ?? 'available'}`
                      : 'Short-term occupation outlook unavailable for this occupation.'}
                  </strong>
                  <span>
                    {occupationTrend?.status === 'available'
                      ? `Cedefop STAS · ${occupationTrend.latest_period} · ${occupationTrend.latest_growth_pct?.toFixed(1)}% published employment growth. This is occupation employment outlook, not OJA skill-demand growth.`
                      : 'AUGUR has no verified short-term occupation outlook for the resolved ISCO group.'}
                  </span>
                  <small>
                    Skill-demand time series: {skillDemandTrend?.status === 'source_access_gated'
                      ? 'source access gated via Eurostat microdata'
                      : skillDemandTrend?.status ?? 'unavailable'}.
                  </small>
                </div>
              ) : tab === 'languages' ? (
                <div className="evidenceUnavailable">
                  <strong>
                    {languageOjaRequirements?.status === 'source_access_gated'
                      ? 'Job-ad language demand is source-access gated.'
                      : 'Job-ad language demand is unavailable.'}
                  </strong>
                  <span>
                    Skills-OVATE detailed OJA data are accessed through Eurostat microdata. AUGUR does not scrape the Tableau dashboard or infer language-demand shares from ESCO.
                  </span>
                </div>
              ) : (
                <div className="skillsTableWrap">
                  <table className="skillsDemandTable">
                    <thead><tr><th>Skill</th><th>Demand</th><th>Trend</th><th>Evidence</th><th>Your profile</th><th>Match</th></tr></thead>
                    <tbody>
                      {visibleSkills.map((skill) => {
                        const declared = (profile?.skills ?? []).some((item) => item.toLowerCase() === skill.toLowerCase())
                        const essentialMatch = matched.some((item) => item.toLowerCase() === skill.toLowerCase())
                        const gap = missing.some((item) => item.toLowerCase() === skill.toLowerCase())
                        return (
                          <tr key={skill}>
                            <td><strong>{skill}</strong></td>
                            <td>{liveSkillDemandAvailable ? 'Available' : 'Not yet measured'}</td>
                            <td>—</td>
                            <td>{essentialMatch || gap ? 'ESCO occupation evidence' : 'Declared profile skill'}</td>
                            <td>{declared ? 'Declared' : 'Not declared'}</td>
                            <td><span className={essentialMatch ? 'evidenceChip good' : gap ? 'evidenceChip warn' : 'evidenceChip neutral'}>{essentialMatch ? 'Matched' : gap ? 'Gap' : 'Context'}</span></td>
                          </tr>
                        )
                      })}
                      {visibleSkills.length === 0 && <tr><td colSpan={6}>No skill evidence available for this view.</td></tr>}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="skillsEvidenceFooter">
                <div><span>Occupation market signal</span><strong>{career?.market_signal?.replaceAll('_', ' ') ?? 'Unavailable'}</strong></div>
                <div><span>Vacancy context</span><strong>{demandEvidenceAvailable ? demandEvidenceLabel : demandCoverageUnavailable ? 'Source coverage unavailable' : 'Unavailable'}</strong></div>
                <div><span>Skill coverage</span><strong>{career?.skill_match?.coverage == null ? 'Unavailable' : `${Math.round(career.skill_match.coverage * 100)}% essential skills`}</strong></div>
              </div>

              <section className="demandEvidenceCoverage" aria-label="Demand evidence coverage">
                <div className="panelHeading">
                  <div>
                    <span>DEMAND EVIDENCE COVERAGE</span>
                    <h3>What is measured vs. still pending</h3>
                  </div>
                </div>
                <div className="demandCoverageGrid">
                  <article className="active">
                    <span>ACTIVE</span>
                    <strong>Current shortage / surplus</strong>
                    <small>EURES / ELA occupation evidence</small>
                  </article>
                  <article className="active">
                    <span>ACTIVE</span>
                    <strong>Vacancy context</strong>
                    <small>Eurostat experimental JVR by occupation group</small>
                  </article>
                  <article className="active">
                    <span>ACTIVE</span>
                    <strong>Occupation-skill relationships</strong>
                    <small>ESCO taxonomy · not demand frequency</small>
                  </article>
                  <article className="planned">
                    <span>PLANNED</span>
                    <strong>Future shortage pressure</strong>
                    <small>Cedefop CLSSI 2026 · country / occupation to 2035</small>
                  </article>
                  <article className={occupationTrend?.status === 'available' ? 'active' : 'planned'}>
                    <span>{occupationTrend?.status === 'available' ? 'ACTIVE' : 'PLANNED'}</span>
                    <strong>Short-term occupation outlook</strong>
                    <small>
                      {occupationTrend?.status === 'available'
                        ? `Cedefop STAS · ${occupationTrend.latest_period} · ${occupationTrend.latest_growth_pct?.toFixed(1)}% employment growth · ${occupationTrend.direction?.replaceAll('_', ' ')}`
                        : 'Cedefop STAS · occupation outlook not available for this resolved ISCO group'}
                    </small>
                  </article>
                  <article className={eu27OjaImbalance?.status === 'available' ? 'active' : 'planned'}>
                    <span>{eu27OjaImbalance?.status === 'available' ? 'ACTIVE · EU27' : 'PLANNED'}</span>
                    <strong>OJA recruitment pressure</strong>
                    <small>
                      {eu27OjaImbalance?.status === 'available' && eu27OjaImbalance.score != null
                        ? `Cedefop exploratory score · ${eu27OjaImbalance.score.toFixed(3)} · ISCO-4 ${eu27OjaImbalance.isco08 ?? ''}`
                        : 'Cedefop OJA imbalance · exact ISCO-4 context'}
                    </small>
                  </article>
                  <article className="restricted">
                    <span>{skillDemandTrend?.status === 'source_access_gated' ? 'SOURCE ACCESS GATED' : 'ACCESS NEEDED'}</span>
                    <strong>Skill demand shares / trends</strong>
                    <small>Cedefop Skills-OVATE detailed OJA evidence · Eurostat microdata access</small>
                  </article>
                  <article className="restricted">
                    <span>{languageOjaRequirements?.status === 'source_access_gated' ? 'SOURCE ACCESS GATED' : 'ACCESS NEEDED'}</span>
                    <strong>Job-ad language demand</strong>
                    <small>Cedefop Skills-OVATE detailed OJA evidence · no Tableau scraping</small>
                  </article>
                </div>
              </section>
            </>
          )}
        </section>
        <aside className="languageDemandPanel">
          <section>
            <div className="panelHeading">
              <div>
                <span>LANGUAGE FIT</span>
                <h3>Declared + target evidence</h3>
              </div>
            </div>

            <div className="languageEvidenceTable">
              {(language?.matches ?? []).map((item) => (
                <div key={item.language}>
                  <strong>{item.language}</strong>
                  <span>{item.meets_work_ready_heuristic ? 'Meets AUGUR work-ready heuristic' : 'Gap / evidence incomplete'}</span>
                  <small>Your level: {item.declared_cefr ?? languageLevel(profile, item.language)}</small>
                </div>
              ))}
              {(language?.matches ?? []).length === 0 && (
                <div><span>No target-language evidence available.</span></div>
              )}
            </div>
          </section>

          <section className="learningEffortPanel">
            <div className="panelHeading">
              <div>
                <span>LEARNING EFFORT</span>
                <h3>Estimate status</h3>
              </div>
            </div>
            <p>
              CEFR learning-time estimates live in TTV and require a declared current level plus weekly study hours.
              This page does not invent hours when those inputs are missing.
            </p>
          </section>

          <section className="skillsInsightPanel">
            <div className="panelHeading">
              <div>
                <span>INSIGHTS</span>
                <h3>What AUGUR can say now</h3>
              </div>
            </div>
            <ul>
              <li>Occupation: {career?.occupation_match?.selected?.preferred_label ?? 'not confidently resolved'}.</li>
              <li>Market signal: {career?.market_signal?.replaceAll('_', ' ') ?? 'not available'}{career?.market_signal_isco ? ` · ISCO ${career.market_signal_isco}` : ''}.</li>
              <li>Market evidence: {career?.source?.label ?? 'not available'}{career?.source?.conditions_year ? ` · ${career.source.conditions_year} conditions` : ''}{career?.source?.evidence_id ? ` · ${career.source.evidence_id}` : ''}.</li>
              <li>Vacancy context: {career?.vacancy_demand_evidence?.status === 'available'
                    ? `Eurostat ${career.vacancy_demand_evidence.period} · ISCO ${career.vacancy_demand_evidence.isco_3digit ?? career.vacancy_demand_evidence.isco_major ?? career.vacancy_demand_evidence.granularity ?? 'group'} vacancy rate ${career.vacancy_demand_evidence.vacancy_rate_pct?.toFixed(1)}% · context only`
                    : career?.vacancy_demand_evidence?.status === 'source_coverage_unavailable'
                    ? `Eurostat experimental ISCO-3 source does not cover ${countryName}; this is not zero demand`
                    : 'not available'}.</li>
              <li>Skill evidence: {career?.skill_match?.dataset_version ?? career?.skill_match?.dataset_mode ?? 'not available'}.</li>
              <li>Live skill demand, employer counts and rising-skill trends are intentionally withheld until a job-posting evidence source is integrated.</li>
            </ul>
          </section>
        </aside>
      </div>
    </section>
  )
}
