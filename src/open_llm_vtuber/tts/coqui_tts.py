import os
import threading
from typing import Optional

import soundfile as sf
from cached_path import cached_path
from f5_tts.api import F5TTS
from loguru import logger

from .tts_interface import TTSInterface

CKPT = "hf://Misha24-10/F5-TTS_RUSSIAN/F5TTS_v1_Base/model_240000_inference.safetensors"
VOCAB = "hf://Misha24-10/F5-TTS_RUSSIAN/F5TTS_v1_Base/vocab.txt"

# --- Tuning knobs ---
NFE_STEP = 24        # quality vs speed: 16 fast, 24 balanced, 32 best
SPEED = 0.95         # < 1.0 = slightly slower speech
TAIL_MARGIN = 1.15   # +15% duration so word endings are not cut off
MIN_GEN_SEC = 1.0    # minimum length for very short phrases like "Ой!"


class TTSEngine(TTSInterface):
    """F5-TTS Russian engine, plugged in under the 'coqui_tts' name."""

    _lock = threading.Lock()

    def __init__(
        self,
        model_name: Optional[str] = None,
        speaker_wav: Optional[str] = None,
        language: Optional[str] = "ru",
        device: Optional[str] = None,
    ):
        self.device = device or "cuda"
        self.ref_file = speaker_wav

        txt_path = os.path.splitext(speaker_wav)[0] + ".txt"
        with open(txt_path, encoding="utf-8") as f:
            self.ref_text = f.read().strip()

        # Reference stats used to estimate how long a new phrase should be
        self.ref_dur = sf.info(speaker_wav).duration
        self.ref_len = max(len(self.ref_text.encode("utf-8")), 1)

        ckpt = str(cached_path(CKPT))
        vocab = str(cached_path(VOCAB))
        self.tts = F5TTS(
            model="F5TTS_v1_Base", ckpt_file=ckpt, vocab_file=vocab, device=self.device
        )
        logger.info(
            f"F5-TTS loaded on {self.device}, reference: {self.ref_file} "
            f"({self.ref_dur:.1f}s)"
        )

    def _total_duration(self, text: str) -> float:
        """Reference + generated duration in seconds, with a safety margin."""
        gen_len = len(text.encode("utf-8"))
        estimated = self.ref_dur * gen_len / self.ref_len / SPEED
        generated = max(estimated * TAIL_MARGIN, MIN_GEN_SEC)
        return self.ref_dur + generated

    def generate_audio(self, text: str, file_name_no_ext: Optional[str] = None) -> str:
        output_path = self.generate_cache_file_name(file_name_no_ext, "wav")

        clean = text.strip()
        if clean and clean[-1] not in ".!?…,":
            clean += "."

        try:
            with self._lock:
                self.tts.infer(
                    ref_file=self.ref_file,
                    ref_text=self.ref_text,
                    gen_text=clean,
                    file_wave=output_path,
                    nfe_step=NFE_STEP,
                    fix_duration=self._total_duration(clean),
                    show_info=lambda *a, **k: None,
                )
            return output_path
        except Exception as e:
            logger.error(f"F5-TTS failed on text: {text!r}")
            raise RuntimeError(f"Failed to generate audio: {str(e)}")