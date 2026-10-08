from __future__ import annotations

import json
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx


LANDING_URL = (
    "https://www.oecd.org/en/data/datasets/"
    "oecd-definition-of-cities-and-functional-urban-areas.html"
)


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        attrs_map = dict(attrs)
        self._href = attrs_map.get("href")
        self._text_parts = []

    def handle_data(self, data):
        if self._href is not None:
            self._text_parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() != "a" or self._href is None:
            return
        text = " ".join("".join(self._text_parts).split())
        self.links.append((self._href, text))
        self._href = None
        self._text_parts = []


def _candidate_links(html_text: str) -> list[dict]:
    parser = LinkCollector()
    parser.feed(html_text)
    candidates = []
    seen = set()

    for href, text in parser.links:
        absolute = urljoin(LANDING_URL, href)
        lowered = f"{absolute} {text}".lower()
        if not (
            ".gpkg" in lowered
            or ".zip" in lowered
            or "boundar" in lowered
            or "functional urban" in lowered
            or "cities" in lowered
        ):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        candidates.append({
            "url": absolute,
            "text": text,
        })
    return candidates


def main() -> int:
    with httpx.Client(
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
        headers={"User-Agent": "AUGUR/0.1"},
    ) as client:
        landing = client.get(LANDING_URL)
        landing.raise_for_status()
        candidates = _candidate_links(landing.text)

        inspected = []
        for candidate in candidates:
            url = candidate["url"]
            path = urlparse(url).path.lower()
            if not (
                path.endswith(".gpkg")
                or path.endswith(".zip")
                or "boundar" in url.lower()
                or "cities" in candidate["text"].lower()
                or "fua" in candidate["text"].lower()
            ):
                continue

            try:
                response = client.head(url)
                if response.status_code in {405, 501}:
                    response = client.get(
                        url,
                        headers={"Range": "bytes=0-0"},
                    )
                inspected.append({
                    **candidate,
                    "http_status": response.status_code,
                    "resolved_url": str(response.request.url),
                    "content_type": response.headers.get("content-type"),
                    "content_length": response.headers.get("content-length"),
                    "accept_ranges": response.headers.get("accept-ranges"),
                    "looks_like_gpkg": ".gpkg" in str(response.request.url).lower(),
                    "looks_like_archive": (
                        ".zip" in str(response.request.url).lower()
                        or "zip" in str(response.headers.get("content-type") or "").lower()
                    ),
                })
            except httpx.HTTPError as exc:
                inspected.append({
                    **candidate,
                    "status": "request_failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                })

    viable = [
        item
        for item in inspected
        if item.get("http_status") in {200, 206}
        and (item.get("looks_like_gpkg") or item.get("looks_like_archive"))
    ]

    payload = {
        "source_id": "OECD",
        "geography_system": "OECD_FUA",
        "landing_url": LANDING_URL,
        "landing_http_status": landing.status_code,
        "candidate_count": len(candidates),
        "inspected": inspected,
        "viable_geometry_links": viable,
        "ready_for_geometry_download": bool(viable),
    }
    print(json.dumps(payload, indent=2, default=str))

    # Link discovery itself is useful even when hosted-runner transport
    # restrictions prevent the archive from being downloaded.
    return 0 if candidates else 2


if __name__ == "__main__":
    raise SystemExit(main())
