from io import BytesIO

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from .config import MAX_AUDIO_SECONDS, TARGET_SAMPLE_RATE


class AudioInputError(ValueError):
    pass


def decode_audio(content: bytes) -> tuple[np.ndarray, int]:
    """Decode an uploaded audio file and return mono 16 kHz float32 samples."""
    if not content:
        raise AudioInputError("The audio file is empty.")
    try:
        waveform, sample_rate = sf.read(BytesIO(content), dtype="float32", always_2d=True)
    except Exception as exc:
        raise AudioInputError("The audio could not be read. Upload WAV, FLAC, or a browser-supported audio file.") from exc

    if waveform.size == 0 or sample_rate <= 0:
        raise AudioInputError("The audio file contains no samples to analyze.")
    waveform = np.nan_to_num(waveform, nan=0.0, posinf=0.0, neginf=0.0)
    waveform = waveform.mean(axis=1)
    if sample_rate != TARGET_SAMPLE_RATE:
        divisor = int(np.gcd(sample_rate, TARGET_SAMPLE_RATE))
        waveform = resample_poly(
            waveform,
            TARGET_SAMPLE_RATE // divisor,
            sample_rate // divisor,
        ).astype(np.float32)
        sample_rate = TARGET_SAMPLE_RATE

    max_samples = int(MAX_AUDIO_SECONDS * TARGET_SAMPLE_RATE)
    if waveform.shape[0] > max_samples:
        waveform = waveform[:max_samples]
    if waveform.shape[0] < int(0.25 * TARGET_SAMPLE_RATE):
        raise AudioInputError("The audio is too short. Upload at least 0.25 seconds.")
    peak = float(np.max(np.abs(waveform)))
    if peak < 1e-5:
        raise AudioInputError("The audio is nearly silent, so reliable recognition is not possible.")
    return waveform.astype(np.float32), sample_rate
