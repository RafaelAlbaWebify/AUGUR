import FlagIcon from './FlagIcon'

type Country = {
  iso3: string
  name: string
}

type CountrySelectProps = {
  countries: Country[]
  value: string
  onChange: (iso3: string) => void
  ariaLabel: string
  compact?: boolean
}

export default function CountrySelect({
  countries,
  value,
  onChange,
  ariaLabel,
  compact = false,
}: CountrySelectProps) {
  return (
    <label className={compact ? 'countryPicker compact' : 'countryPicker'}>
      <FlagIcon iso3={value} />
      <select
        value={value}
        aria-label={ariaLabel}
        onChange={(event) => onChange(event.target.value)}
      >
        {countries.map((country) => (
          <option value={country.iso3} key={country.iso3}>
            {country.name}
          </option>
        ))}
      </select>
      <span className="countryPickerChevron">⌄</span>
    </label>
  )
}
