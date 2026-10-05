#!/usr/bin/env python3
"""Collect an independent, license-verified HearAround holdout set.

The source IDs in this file are intentionally disjoint from data/manifest.csv.
Only Freesound pages that explicitly expose the CC0 deed are accepted.  The
normalized audio is a local evaluation artifact and is not served by the app.
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import re
import shutil
import subprocess
import time
from datetime import date
from pathlib import Path

import numpy as np
import requests
import soundfile as sf
from requests.adapters import HTTPAdapter
from scipy.signal import resample_poly
from urllib3.util.retry import Retry


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "eval/source"
AUDIO_DIR = ROOT / "eval/holdout_audio"
MANIFEST = ROOT / "eval/holdout_manifest.csv"
ATTRIBUTION = ROOT / "eval/HOLDOUT_ATTRIBUTION.md"
DEMO_MANIFEST = ROOT / "data/manifest.csv"
TARGET_RATE = 16_000
MAX_SECONDS = 5.0
USER_AGENT = "HearAroundHackathon/0.4 (independent accessibility evaluation)"

# Every item is a different recording and creator/source ID from the demo set.
# Negative items resemble alerts or common home sounds but should not map to a
# HearAround product event.
ASSETS = [
    {"clip_id": "holdout_fire_taurindb", "label": "fire_alarm", "creator": "taurindb", "sound_id": 182401},
    {"clip_id": "holdout_fire_ken788", "label": "fire_alarm", "creator": "ken788", "sound_id": 386756},
    {"clip_id": "holdout_fire_hospital", "label": "fire_alarm", "creator": "nigelcoop", "sound_id": 210513},
    {"clip_id": "holdout_siren_vintage", "label": "emergency_siren", "creator": "craigsmith", "sound_id": 438698},
    {"clip_id": "holdout_siren_passing", "label": "emergency_siren", "creator": "LanDub", "sound_id": 184623},
    {"clip_id": "holdout_siren_swedish", "label": "emergency_siren", "creator": "Nahlin83", "sound_id": 220424},
    {"clip_id": "holdout_horn_danlucaz", "label": "car_horn", "creator": "danlucaz", "sound_id": 517673},
    {"clip_id": "holdout_horn_devern", "label": "car_horn", "creator": "DeVern", "sound_id": 349922},
    {"clip_id": "holdout_horn_small", "label": "car_horn", "creator": "tm1000", "sound_id": 94868},
    {"clip_id": "holdout_baby_short", "label": "baby_crying", "creator": "deleted_user_2104797", "sound_id": 346663},
    {"clip_id": "holdout_baby_room", "label": "baby_crying", "creator": "Julien_Matthey", "sound_id": 167078},
    {"clip_id": "holdout_doorbell_marlo", "label": "doorbell", "creator": "marlocarlo", "sound_id": 841813},
    {"clip_id": "holdout_doorbell_digital", "label": "doorbell", "creator": "vdr3", "sound_id": 393333},
    {"clip_id": "holdout_doorbell_shop", "label": "doorbell", "creator": "BlackNeon1234", "sound_id": 348322},
    {"clip_id": "holdout_knock_samuel", "label": "knocking", "creator": "SamuelGremaud", "sound_id": 426736},
    {"clip_id": "holdout_knock_ultra", "label": "knocking", "creator": "Ultra-Edward", "sound_id": 789382},
    {"clip_id": "holdout_knock_timmeh", "label": "knocking", "creator": "Timmeh515", "sound_id": 413270},
    {"clip_id": "negative_dog_bark", "label": "none", "creator": "Jace", "sound_id": 155312},
    {"clip_id": "negative_alarm_clock", "label": "none", "creator": "xyzr_kx", "sound_id": 14262},
    {"clip_id": "negative_audience_laugh", "label": "none", "creator": "schots", "sound_id": 452750},
    {"clip_id": "negative_phone_digital", "label": "none", "creator": "ZoshP", "sound_id": 541796},
    {"clip_id": "negative_dishes", "label": "none", "creator": "Nomadyag", "sound_id": 193060},
    {"clip_id": "negative_phone_bell", "label": "none", "creator": "DrNI", "sound_id": 164036},
]

FIELDS = [
    "clip_id", "expected_label", "source_url", "source_site", "creator",
    "license", "license_url", "attribution", "downloaded_at", "split",
    "duration_s", "source_id", "policy_version", "notes",
]

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})
SESSION.mount("https://", HTTPAdapter(max_retries=Retry(
    total=4,
    connect=4,
    read=4,
    backoff_factor=1.0,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=("GET",),
)))


def plain(value: str | None) -> str:
    value = html.unescape(value or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def demo_source_ids() -> set[int]:
    if not DEMO_MANIFEST.exists():
        return set()
    text = DEMO_MANIFEST.read_text(encoding="utf-8")
    return {int(value) for value in re.findall(r"freesound\.org/people/[^/]+/sounds/(\d+)/", text)}


def validate_partition() -> None:
    ids = [asset["sound_id"] for asset in ASSETS]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Holdout contains duplicate source IDs.")
    overlap = set(ids) & demo_source_ids()
    if overlap:
        raise RuntimeError(f"Holdout/demo source leakage detected: {sorted(overlap)}")


def fetch_metadata(asset: dict) -> dict:
    page_url = f"https://freesound.org/people/{asset['creator']}/sounds/{asset['sound_id']}/"
    response = SESSION.get(page_url, timeout=45)
    response.raise_for_status()
    page = response.text
    if "creativecommons.org/publicdomain/zero/1.0/" not in page or "Creative Commons 0" not in page:
        raise RuntimeError(f"Source page is not explicitly verified CC0: {page_url}")
    previews = sorted(set(re.findall(
        r"https://cdn\.freesound\.org/previews/[^\"' ]+?\.(?:mp3|ogg)", page,
    )))
    if not previews:
        raise RuntimeError(f"No public preview URL found: {page_url}")
    title_match = re.search(r"<title>Freesound - (.+?) by .+?</title>", page, re.I)
    return {
        "title": plain(title_match.group(1)) if title_match else f"Freesound {asset['sound_id']}",
        "file_url": next((url for url in previews if "-hq.mp3" in url), previews[0]),
        "page_url": page_url,
    }


def download(url: str, target: Path) -> None:
    partial = target.with_name(f"{target.name}.part")
    with SESSION.get(url, timeout=90, stream=True) as response:
        response.raise_for_status()
        partial.unlink(missing_ok=True)
        with partial.open("wb") as handle:
            for chunk in response.iter_content(1024 * 256):
                if chunk:
                    handle.write(chunk)
        if not partial.exists() or partial.stat().st_size == 0:
            raise RuntimeError(f"Empty download: {url}")
        partial.replace(target)


def decode(source: Path) -> tuple[np.ndarray, int]:
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
    return np.nan_to_num(waveform.mean(axis=1)), sample_rate


def normalize(source: Path, target: Path) -> float:
    waveform, sample_rate = decode(source)
    if sample_rate != TARGET_RATE:
        divisor = int(np.gcd(sample_rate, TARGET_RATE))
        waveform = resample_poly(waveform, TARGET_RATE // divisor, sample_rate // divisor).astype(np.float32)
    max_samples = int(MAX_SECONDS * TARGET_RATE)
    if len(waveform) > max_samples:
        energy_window = TARGET_RATE // 4
        squared = np.square(waveform, dtype=np.float64)
        cumulative = np.concatenate(([0.0], np.cumsum(squared)))
        energy = (cumulative[energy_window:] - cumulative[:-energy_window]) / energy_window
        center = int(np.argmax(energy)) + energy_window // 2
        start = min(max(0, center - max_samples // 2), len(waveform) - max_samples)
        waveform = waveform[start:start + max_samples]
    if len(waveform) < TARGET_RATE // 4:
        raise RuntimeError(f"Clip is too short: {source.name}")
    peak = float(np.max(np.abs(waveform)))
    if peak > 0:
        waveform *= 0.7 / peak
    sf.write(target, waveform, TARGET_RATE, subtype="PCM_16")
    return len(waveform) / TARGET_RATE


def write_attribution(rows: list[dict]) -> None:
    lines = [
        "# HearAround independent holdout attribution",
        "",
        "All source pages were checked for CC0 at collection time. The set is disjoint from the demo source IDs and is not served by the product UI.",
        "",
        "| Clip | Expected | Creator | License | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['clip_id']}` | `{row['expected_label']}` | {row['creator']} | "
            f"[{row['license']}]({row['license_url']}) | [source]({row['source_url']}) |"
        )
    ATTRIBUTION.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-normalize", action="store_true")
    args = parser.parse_args()
    validate_partition()
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for asset in ASSETS:
        metadata = fetch_metadata(asset)
        source_path = SOURCE_DIR / f"{asset['clip_id']}{Path(metadata['file_url']).suffix or '.audio'}"
        audio_path = AUDIO_DIR / f"{asset['clip_id']}.wav"
        print(f"collect {asset['clip_id']}: CC0 1.0")
        if not source_path.exists():
            download(metadata["file_url"], source_path)
            time.sleep(1.0)
        duration = normalize(source_path, audio_path) if args.force_normalize or not audio_path.exists() else sf.info(audio_path).duration
        rows.append({
            "clip_id": asset["clip_id"],
            "expected_label": asset["label"],
            "source_url": metadata["page_url"],
            "source_site": "Freesound public preview",
            "creator": asset["creator"],
            "license": "CC0 1.0",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "attribution": f"{metadata['title']} by {asset['creator']} (CC0 1.0)",
            "downloaded_at": date.today().isoformat(),
            "split": "holdout",
            "duration_s": f"{duration:.3f}",
            "source_id": asset["sound_id"],
            "policy_version": "1-frozen-before-holdout",
            "notes": "Independent source; mono 16 kHz PCM WAV; peak normalized; maximum 5 seconds.",
        })
    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    write_attribution(rows)
    print(f"wrote {len(rows)} independent clips to {MANIFEST}")


if __name__ == "__main__":
    main()
