import io
import unittest

import numpy as np
import soundfile as sf

from app.audio import AudioInputError, decode_audio


def wav_bytes(samples: np.ndarray, sample_rate: int) -> bytes:
    buffer = io.BytesIO()
    sf.write(buffer, samples, sample_rate, format="WAV")
    return buffer.getvalue()


class AudioTests(unittest.TestCase):
    def test_stereo_audio_is_mono_and_resampled(self):
        sample_rate = 8_000
        time = np.arange(sample_rate) / sample_rate
        mono = (0.2 * np.sin(2 * np.pi * 440 * time)).astype(np.float32)
        stereo = np.column_stack([mono, mono * 0.5])
        waveform, output_rate = decode_audio(wav_bytes(stereo, sample_rate))
        self.assertEqual(output_rate, 16_000)
        self.assertEqual(waveform.ndim, 1)
        self.assertGreater(len(waveform), 15_900)

    def test_silence_is_rejected(self):
        silence = np.zeros(16_000, dtype=np.float32)
        with self.assertRaises(AudioInputError):
            decode_audio(wav_bytes(silence, 16_000))


if __name__ == "__main__":
    unittest.main()
