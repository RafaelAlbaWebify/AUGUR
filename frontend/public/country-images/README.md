# Country images

AUGUR country hero assets live here and are referenced through `src/lib/countryVisuals.ts`.

## Runtime convention

The UI now looks first for a local production photo:

- `ESP.webp`
- `PRT.webp`
- `IRL.webp`
- future countries: `<ISO3>.webp`

If the WebP is not present, the browser automatically falls back to the checked-in SVG placeholder with the same ISO3 code. This keeps AUGUR fully usable while photography is curated country by country.

Recommended production image requirements:

- 1600×900 minimum
- WebP preferred
- landscape composition
- no embedded text or watermark
- representative urban/landscape context without implying that one city represents the whole country
- licence and source recorded below

## Curated source candidates

These are **source candidates**, not remote runtime dependencies. Downloaded production files should be stored locally in this folder.

### ESP

Candidate: **Sunset, Gran Via, Madrid.jpg**
- Wikimedia Commons
- Author: Gerda Arendt
- Licence: CC0 1.0 / public-domain dedication
- Source page: https://commons.wikimedia.org/wiki/File:Sunset,_Gran_Via,_Madrid.jpg

### PRT

Candidate: **A Lisbon view.jpg**
- Wikimedia Commons
- Author: CrisLuiz
- Licence: CC0 1.0 / public-domain dedication
- Source page: https://commons.wikimedia.org/wiki/File:A_Lisbon_view.jpg

### IRL

Candidate: **GCD Dublin.jpg**
- Wikimedia Commons
- Author: Andreas Wolf 01
- Licence: CC0 1.0 / public-domain dedication
- Source page: https://commons.wikimedia.org/wiki/File:GCD_Dublin.jpg

## Asset policy

AUGUR must not hotlink hero photography from third-party hosts. Production images belong in this directory so the app remains deterministic and local-first. Where attribution is required by a future image licence, preserve it here and surface it in the application if the licence requires visible attribution.
