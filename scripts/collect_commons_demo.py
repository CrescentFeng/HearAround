#!/usr/bin/env python3
"""Download, verify, and normalize the license-cleared HearAround demo set.

The collector intentionally supports more than one public source so a temporary
CDN rate limit cannot make the build irreproducible.  Every source page is
checked at collection time and every derived WAV keeps its provenance in the
manifest.
"""

from __future__ import annotations

import csv
import argparse
import html
import io
import re
import shutil
import subprocess
import time
from datetime import date
from pathlib import Path
from urllib.parse import quote

import numpy as np
import requests
import soundfile as sf
from requests.adapters import HTTPAdapter
from scipy.signal import resample_poly
from urllib3.util.retry import Retry


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data/source"
DEMO_DIR = ROOT / "data/demo"
MANIFEST_PATH = ROOT / "data/manifest.csv"
ATTRIBUTION_PATH = ROOT / "data/ATTRIBUTION.md"
API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "HearAroundHackathon/0.3 (educational accessibility prototype)"
TARGET_RATE = 16_000
MAX_SECONDS = 5.0

ASSETS = [
    {"clip_id": "fire_nfpa", "label": "fire_alarm", "source": "commons", "title": "File:NFPA Fire Alarm.ogg"},
    {"clip_id": "fire_smoke_alarm", "label": "fire_alarm", "source": "commons", "title": "File:Smoke alarm.ogg"},
    {"clip_id": "siren_whelen", "label": "emergency_siren", "source": "commons", "title": "File:Whelen.ogg"},
    {"clip_id": "siren_police_us", "label": "emergency_siren", "source": "commons", "title": "File:American police siren i.ogg"},
    {"clip_id": "horn_car_cc0", "label": "car_horn", "source": "commons", "title": "File:Car Horn.wav"},
    {"clip_id": "horn_postauto", "label": "car_horn", "source": "commons", "title": "File:Postauto (CH) Dreiklanghorn.ogg"},
    {"clip_id": "baby_newborn", "label": "baby_crying", "source": "commons", "title": "File:Crying newborn baby.ogg"},
    {"clip_id": "baby_disappointed", "label": "baby_crying", "source": "commons", "title": "File:Babys disappointed crying.oga"},
    {"clip_id": "doorbell_classic", "label": "doorbell", "source": "freesound", "sound_id": 397919, "creator": "nozefian"},
    {"clip_id": "doorbell_electronic", "label": "doorbell", "source": "freesound", "sound_id": 571674, "creator": "NachtmahrTV"},
    {"clip_id": "doorbell_simple", "label": "doorbell", "source": "freesound", "sound_id": 555016, "creator": "oganesson"},
    {"clip_id": "doorbell_rings", "label": "doorbell", "source": "freesound", "sound_id": 182879, "creator": "LanDub"},
    {"clip_id": "knock_wood", "label": "knocking", "source": "freesound", "sound_id": 458007, "creator": "Fabrizio84"},
    {"clip_id": "knock_knocker", "label": "knocking", "source": "freesound", "sound_id": 452793, "creator": "cloe.king"},
    {"clip_id": "negative_baby_laugh", "label": "none", "source": "freesound", "sound_id": 260774, "creator": "iccleste"},
    {"clip_id": "negative_baby_rattle", "label": "none", "source": "freesound", "sound_id": 42939, "creator": "AGFX"},
    {"clip_id": "negative_kitchen", "label": "none", "source": "freesound", "sound_id": 203533, "creator": "heysticks"},
    {"clip_id": "negative_morse", "label": "none", "source": "freesound", "sound_id": 478969, "creator": "SkibkaMusic"},
]

MIXES = [
    {"clip_id": "mixed_doorbell_baby", "label": "doorbell|baby_crying", "sources": ["doorbell_rings", "baby_disappointed"], "gains": [0.9, 0.35]},
    {"clip_id": "mixed_fire_knock", "label": "fire_alarm|knocking", "sources": ["fire_smoke_alarm", "knock_wood"], "gains": [0.8, 0.5]},
]

FIELDS = ["clip_id", "expected_label", "source_url", "source_site", "creator", "license", "license_url", "attribution", "downloaded_at", "split", "duration_s", "notes"]

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})
SESSION.mount("https://", HTTPAdapter(max_retries=Retry(
    total=4,
    connect=4,
    read=4,
    backoff_factor=1.0,
    status_forcelist=(500, 502, 503, 504),
    allowed_methods=("GET",),
)))


def plain(value: str | None) -> str:
    value = html.unescape(value or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def parse_commons_metadata(page: dict) -> dict:
    if page.get("missing"):
        raise RuntimeError(f"Commons file not found: {page.get('title')}")
    info = page["imageinfo"][0]
    metadata = info.get("extmetadata", {})
    license_name = plain(metadata.get("LicenseShortName", {}).get("value"))
    normalized = license_name.lower().replace("-", " ")
    allowed = "cc0" in normalized or "public domain" in normalized or ("cc by" in normalized and "sa" not in normalized)
    if not allowed:
        raise RuntimeError(f"Disallowed license for {page['title']}: {license_name}")
    return {
        "title": page["title"],
        "file_url": info["url"].split("?")[0],
        "page_url": f"https://commons.wikimedia.org/wiki/{quote(page['title'].replace(' ', '_'))}",
        "mime": info.get("mime", ""),
        "creator": plain(metadata.get("Artist", {}).get("value")) or "Wikimedia Commons contributor",
        "license": license_name,
        "license_url": plain(metadata.get("LicenseUrl", {}).get("value")),
        "source_site": "Wikimedia Commons",
    }


def fetch_commons_metadata(titles: list[str]) -> dict[str, dict]:
    response = SESSION.get(
        API,
        params={
            "action": "query",
            "titles": "|".join(titles),
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|mime|size",
            "format": "json",
            "formatversion": 2,
        },
        timeout=45,
    )
    response.raise_for_status()
    parsed = [parse_commons_metadata(page) for page in response.json()["query"]["pages"]]
    return {item["title"]: item for item in parsed}


def fetch_freesound_metadata(asset: dict) -> dict:
    page_url = f"https://freesound.org/people/{asset['creator']}/sounds/{asset['sound_id']}/"
    response = SESSION.get(page_url, timeout=45)
    response.raise_for_status()
    page = response.text
    cc0_url = "creativecommons.org/publicdomain/zero/1.0/"
    if cc0_url not in page or "Creative Commons 0" not in page:
        raise RuntimeError(f"Freesound page is not verified CC0: {page_url}")
    previews = sorted(set(re.findall(
        r"https://cdn\.freesound\.org/previews/[^\"' ]+?\.(?:mp3|ogg)",
        page,
    )))
    if not previews:
        raise RuntimeError(f"No public preview URL found: {page_url}")
    file_url = next((url for url in previews if "-hq.mp3" in url), previews[0])
    title_match = re.search(r"<title>Freesound - (.+?) by .+?</title>", page, re.I)
    title = plain(title_match.group(1)) if title_match else f"Freesound {asset['sound_id']}"
    return {
        "title": title,
        "file_url": file_url,
        "page_url": page_url,
        "creator": asset["creator"],
        "license": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "source_site": "Freesound public preview",
    }


def fetch_metadata() -> dict[str, dict]:
    commons_assets = [asset for asset in ASSETS if asset["source"] == "commons"]
    by_title = fetch_commons_metadata([asset["title"] for asset in commons_assets])
    result = {asset["clip_id"]: by_title[asset["title"]] for asset in commons_assets}
    for asset in (item for item in ASSETS if item["source"] == "freesound"):
        result[asset["clip_id"]] = fetch_freesound_metadata(asset)
    return result


def download(url: str, target: Path) -> None:
    partial = target.with_name(f"{target.name}.part")
    for attempt in range(1, 4):
        try:
            with SESSION.get(url, timeout=90, stream=True) as response:
                response.raise_for_status()
                remote_size = int(response.headers.get("content-length", "0"))
                if target.exists() and target.stat().st_size > 0:
                    if not remote_size or target.stat().st_size == remote_size:
                        return
                partial.unlink(missing_ok=True)
                with partial.open("wb") as handle:
                    for chunk in response.iter_content(1024 * 256):
                        if chunk:
                            handle.write(chunk)
                if remote_size and partial.stat().st_size != remote_size:
                    raise RuntimeError(
                        f"Incomplete download for {target.name}: "
                        f"{partial.stat().st_size}/{remote_size} bytes"
                    )
                partial.replace(target)
                return
        except (requests.RequestException, RuntimeError):
            partial.unlink(missing_ok=True)
            if attempt == 3:
                raise
            time.sleep(attempt * 2)


def normalize_audio(source: Path, target: Path) -> float:
    try:
        waveform, sample_rate = sf.read(source, dtype="float32", always_2d=True)
    except sf.LibsndfileError:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError(f"FFmpeg is required to decode {source.name}")
        process = subprocess.run(
            [ffmpeg, "-v", "error", "-i", str(source), "-ac", "1", "-ar", str(TARGET_RATE), "-f", "wav", "pipe:1"],
            check=True,
            capture_output=True,
        )
        waveform, sample_rate = sf.read(io.BytesIO(process.stdout), dtype="float32", always_2d=True)
    waveform = np.nan_to_num(waveform.mean(axis=1))
    if sample_rate != TARGET_RATE:
        divisor = int(np.gcd(sample_rate, TARGET_RATE))
        waveform = resample_poly(waveform, TARGET_RATE // divisor, sample_rate // divisor).astype(np.float32)
    max_samples = int(MAX_SECONDS * TARGET_RATE)
    if len(waveform) > max_samples:
        # Select the loudest five-second region.  Public clips often include a
        # spoken slate or long silence before the actual event.
        energy_window = TARGET_RATE // 4
        squared = np.square(waveform, dtype=np.float64)
        cumulative = np.concatenate(([0.0], np.cumsum(squared)))
        local_energy = (cumulative[energy_window:] - cumulative[:-energy_window]) / energy_window
        peak_index = int(np.argmax(local_energy)) + energy_window // 2
        start = min(max(0, peak_index - max_samples // 2), len(waveform) - max_samples)
        waveform = waveform[start:start + max_samples]
    if len(waveform) < TARGET_RATE // 4:
        raise RuntimeError(f"Clip is too short: {source.name}")
    peak = float(np.max(np.abs(waveform)))
    if peak > 0:
        waveform = waveform * (0.7 / peak)
    sf.write(target, waveform, TARGET_RATE, subtype="PCM_16")
    return len(waveform) / TARGET_RATE


def mix_clips(target: Path, sources: list[Path], gains: list[float]) -> float:
    waveforms = [sf.read(path, dtype="float32")[0] for path in sources]
    length = max(len(waveform) for waveform in waveforms)
    mixed = np.zeros(length, dtype=np.float32)
    for waveform, gain in zip(waveforms, gains, strict=True):
        mixed[:len(waveform)] += waveform * gain
    peak = float(np.max(np.abs(mixed)))
    if peak > 0.95:
        mixed *= 0.95 / peak
    sf.write(target, mixed, TARGET_RATE, subtype="PCM_16")
    return len(mixed) / TARGET_RATE


def write_attribution(rows: list[dict]) -> None:
    lines = [
        "# HearAround demo audio attribution",
        "",
        "Generated from `data/manifest.csv`. Files are normalized derivatives used for the local demo and pipeline smoke test.",
        "",
        "| Clip | Creator | License | Source |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        sources = [item.strip() for item in row["source_url"].split("|") if item.strip()]
        source_links = "<br>".join(f"[source {index}]({url})" for index, url in enumerate(sources, 1))
        creator = row["creator"].replace("|", "\\|")
        license_name = row["license"].replace("|", "\\|")
        lines.append(f"| `{row['clip_id']}` | {creator} | {license_name} | {source_links} |")
    ATTRIBUTION_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-normalize", action="store_true", help="Rebuild WAV files from cached sources.")
    args = parser.parse_args()
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    metadata_by_id = fetch_metadata()
    rows = []
    normalized_paths: dict[str, Path] = {}
    for asset in ASSETS:
        metadata = metadata_by_id[asset["clip_id"]]
        suffix = Path(metadata["file_url"]).suffix or ".audio"
        source_path = SOURCE_DIR / f"{asset['clip_id']}{suffix}"
        demo_path = DEMO_DIR / f"{asset['clip_id']}.wav"
        print(f"collect {asset['clip_id']}: {metadata['license']}")
        if source_path.exists() and demo_path.exists() and not args.force_normalize:
            duration = sf.info(demo_path).duration
        else:
            was_missing = not source_path.exists()
            download(metadata["file_url"], source_path)
            if was_missing:
                time.sleep(1.25)
            duration = normalize_audio(source_path, demo_path)
        normalized_paths[asset["clip_id"]] = demo_path
        rows.append({
            "clip_id": asset["clip_id"],
            "expected_label": asset["label"],
            "source_url": metadata["page_url"],
            "source_site": metadata["source_site"],
            "creator": metadata["creator"],
            "license": metadata["license"],
            "license_url": metadata["license_url"],
            "attribution": f"{metadata['title']} by {metadata['creator']} ({metadata['license']})",
            "downloaded_at": date.today().isoformat(),
            "split": "demo",
            "duration_s": f"{duration:.3f}",
            "notes": "Public source/preview converted to mono 16 kHz PCM WAV; peak normalized; maximum 5 seconds.",
        })

    for mix in MIXES:
        target = DEMO_DIR / f"{mix['clip_id']}.wav"
        source_paths = [normalized_paths[item] for item in mix["sources"]]
        duration = mix_clips(target, source_paths, mix["gains"])
        source_rows = [next(row for row in rows if row["clip_id"] == item) for item in mix["sources"]]
        rows.append({
            "clip_id": mix["clip_id"],
            "expected_label": mix["label"],
            "source_url": " | ".join(row["source_url"] for row in source_rows),
            "source_site": "HearAround derived demo mix",
            "creator": " + ".join(row["creator"] for row in source_rows),
            "license": " + ".join(row["license"] for row in source_rows),
            "license_url": " | ".join(row["license_url"] for row in source_rows),
            "attribution": "Mixed from: " + " | ".join(row["attribution"] for row in source_rows),
            "downloaded_at": date.today().isoformat(),
            "split": "demo_mixed",
            "duration_s": f"{duration:.3f}",
            "notes": f"Derived mix; gains={mix['gains']}; mono 16 kHz PCM WAV.",
        })

    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    write_attribution(rows)
    print(f"wrote {len(rows)} clips, {MANIFEST_PATH}, and {ATTRIBUTION_PATH}")


if __name__ == "__main__":
    main()
