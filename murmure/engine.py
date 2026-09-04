"""Coeur de transcription. Utilisable en local (in-process) ou exposé en
serveur (phase 3). Le client appelle simplement `transcribe(audio)`."""
import os
import sys
from pathlib import Path

import numpy as np


def _add_cuda_dll_dirs() -> None:
    """Sur Windows, ctranslate2 (faster-whisper) a besoin des DLL cuBLAS/cuDNN
    installées via les paquets pip nvidia-*. On les ajoute au chemin de
    recherche des DLL avant tout import de ctranslate2."""
    if sys.platform != "win32":
        return
    base = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
    for sub in ("cublas/bin", "cudnn/bin"):
        p = base / sub
        if p.is_dir():
            try:
                os.add_dll_directory(str(p))
            except OSError:
                pass


class LocalEngine:
    """Transcription locale via faster-whisper."""

    def __init__(self, model="large-v3-turbo", device="cuda",
                 compute_type="float16", language="fr", clean_fillers=True,
                 initial_prompt=None, replacements=None, vocabulary=None):
        _add_cuda_dll_dirs()
        from faster_whisper import WhisperModel  # import tardif (DLL prêtes)

        self.language = language
        self.clean_fillers = clean_fillers
        self.replacements = replacements
        self.vocabulary = vocabulary or []
        # l'amorce Whisper = phrase de base + vocabulaire utilisateur
        prompt = initial_prompt or ""
        if vocabulary:
            prompt = (prompt + " Vocabulaire : " + ", ".join(vocabulary)).strip()
        self.initial_prompt = prompt or None
        try:
            self.model = WhisperModel(model, device=device,
                                      compute_type=compute_type)
            self.device = device
        except Exception as exc:  # repli CPU si le GPU n'est pas dispo
            if device == "cuda":
                print(f"[engine] GPU indisponible ({exc!r}) -> repli CPU int8")
                self.model = WhisperModel(model, device="cpu",
                                          compute_type="int8")
                self.device = "cpu"
            else:
                raise

    def transcribe(self, audio: np.ndarray) -> str:
        """audio : float32 mono 16 kHz, dans [-1, 1]."""
        if audio is None or len(audio) == 0:
            return ""
        segments, _info = self.model.transcribe(
            audio,
            language=self.language,
            beam_size=5,
            vad_filter=True,
            initial_prompt=self.initial_prompt,
        )
        text = "".join(seg.text for seg in segments).strip()
        from .clean import clean_text, enforce_vocab
        text = clean_text(text, remove_fillers=self.clean_fillers,
                          replacements=self.replacements)
        # casse exacte du vocabulaire : appliquée ici pour rester effective
        # même quand la correction LLM est désactivée (mode CPU / PC pro)
        return enforce_vocab(text, self.vocabulary)
