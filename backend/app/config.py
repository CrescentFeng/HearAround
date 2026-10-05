from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
STATIC_DIR = PROJECT_ROOT / "dist"
DATA_DIR = PROJECT_ROOT / "data"
SUBMISSION_DIR = PROJECT_ROOT / "submission"

MAX_AUDIO_BYTES = 25 * 1024 * 1024
MAX_AUDIO_SECONDS = 30.0
TARGET_SAMPLE_RATE = 16_000
YAMNET_URL = "https://tfhub.dev/google/yamnet/1"
YAMNET_CACHE_DIR = PROJECT_ROOT / ".cache" / "tfhub"
