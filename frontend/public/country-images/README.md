# Country images

AUGUR country visuals live here and are referenced through `src/lib/countryVisuals.ts`.

Naming convention:

- `ESP.*`
- `PRT.*`
- `IRL.*`
- future countries use their ISO3 code

The current SVG assets are local starter visuals so the UI never depends on an external image host. They can be replaced with licensed JPG/WebP photography later without changing the Overview component; update only the manifest path when the extension changes.

Recommended production photo requirements:

- 1600×900 minimum
- WebP preferred
- landscape, no text/watermark
- representative but not stereotyped
- documented licence/source in this folder
