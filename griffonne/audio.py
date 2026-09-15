"""Capture micro via sounddevice. Renvoie un tableau float32 mono 16 kHz,
directement consommable par faster-whisper (sans fichier WAV temporaire)."""
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000


class Recorder:
    def __init__(self, samplerate: int = SAMPLE_RATE, device=None):
        self.sr = samplerate
        self.device = device  # index de périphérique, ou None = défaut
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self.recording = False

    def _callback(self, indata, frames, time, status):  # noqa: ARG002
        if status:
            print(f"[audio] {status}")
        self._frames.append(indata.copy())

    def start(self) -> None:
        self._frames = []
        self._stream = sd.InputStream(
            samplerate=self.sr, channels=1, dtype="float32",
            device=self.device, callback=self._callback,
        )
        self._stream.start()
        self.recording = True

    def stop(self) -> np.ndarray:
        self.recording = False
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if not self._frames:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(self._frames, axis=0).flatten()
