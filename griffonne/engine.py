"""Coeur de transcription. Utilisable en local (in-process) ou exposé en
serveur (phase 3). Le client appelle simplement `transcribe(audio)`."""
import os
import sys
from pathlib import Path

import numpy as np


def _add_cuda_dll_dirs() -> None:
    """Sur Windows, ctranslate2 (faster-whisper) et ONNX Runtime (Parakeet)
    ont besoin des DLL CUDA installées via les paquets pip nvidia-*. On ajoute
    tous leurs dossiers `bin` au chemin de recherche des DLL."""
    if sys.platform != "win32":
        return
    base = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
    if not base.is_dir():
        return
    for p in base.glob("*/bin"):
        try:
            os.add_dll_directory(str(p))
        except OSError:
            pass


def _postprocess(text: str, clean_fillers: bool, replacements, vocabulary) -> str:
    """Post-traitement commun à tous les moteurs : hésitations, remplacements
    déterministes, puis casse exacte du vocabulaire (effective même sans LLM)."""
    from .clean import clean_text, enforce_vocab
    text = clean_text(text, remove_fillers=clean_fillers, replacements=replacements)
    return enforce_vocab(text, vocabulary)


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
        return _postprocess(text, self.clean_fillers, self.replacements,
                            self.vocabulary)


class ParakeetEngine:
    """Transcription via NVIDIA Parakeet TDT 0.6B v3 (onnx-asr / ONNX Runtime).

    Modèle 10x plus petit que Whisper large : très rapide sur CPU (~0,4 s),
    encore plus en CUDA (~0,2 s). Contreparties : langue auto-détectée (pas
    de langue forcée) et pas d'amorce par vocabulaire — le vocabulaire agit en
    post-traitement (casse exacte) et via la correction LLM."""

    MODEL = "nemo-parakeet-tdt-0.6b-v3"

    def __init__(self, device="auto", clean_fillers=True, replacements=None,
                 vocabulary=None, **_ignored):
        _add_cuda_dll_dirs()
        import onnx_asr
        import onnxruntime as ort
        ort.set_default_logger_severity(3)  # silence les avertissements ORT

        self.clean_fillers = clean_fillers
        self.replacements = replacements
        self.vocabulary = vocabulary or []

        want_cuda = (device in ("auto", "cuda")
                     and "CUDAExecutionProvider" in ort.get_available_providers())
        providers = (["CUDAExecutionProvider", "CPUExecutionProvider"]
                     if want_cuda else ["CPUExecutionProvider"])
        self.model = onnx_asr.load_model(self.MODEL, providers=providers)
        self.device = "cuda" if want_cuda else "cpu"

    def transcribe(self, audio: np.ndarray) -> str:
        if audio is None or len(audio) == 0:
            return ""
        text = self.model.recognize(np.ascontiguousarray(audio, dtype=np.float32))
        return _postprocess((text or "").strip(), self.clean_fillers,
                            self.replacements, self.vocabulary)


def make_engine(engine: str, **kwargs):
    """Fabrique : 'whisper' (défaut) ou 'parakeet'."""
    if engine == "parakeet":
        return ParakeetEngine(**kwargs)
    return LocalEngine(**kwargs)
