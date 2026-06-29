"""Backends de traitement audio → texte, interface unique `process(audio)`.

- LocalBackend  : transcription + correction in-process (GPU/CPU).
- RemoteBackend : envoie l'audio à un serveur distant (PC GPU) qui fait tout.

Le même LocalBackend sert à l'app locale ET au serveur distant."""
import json
import urllib.request

import numpy as np


class LocalBackend:
    def __init__(self, cfg: dict, vocabulary: list[str]):
        from .devices import resolve_device
        device, compute = resolve_device(cfg["device"], cfg["compute_type"])

        from .engine import LocalEngine
        self.engine = LocalEngine(
            model=cfg["model"], device=device, compute_type=compute,
            language=cfg["language"], clean_fillers=cfg["clean_fillers"],
            initial_prompt=cfg["initial_prompt"], replacements=cfg["replacements"],
            vocabulary=vocabulary,
        )
        self.device = self.engine.device

        self.corrector = None
        if cfg.get("llm_correct", True):
            from .llm import Corrector
            self.corrector = Corrector(
                model=cfg["llm_model"], mode=cfg["llm_mode"],
                url=cfg["ollama_url"], vocabulary=vocabulary,
            )
        self.llm_min_words = cfg.get("llm_min_words", 0)

    def warmup(self) -> None:
        if self.corrector is not None:
            self.corrector.warmup()

    def process(self, audio: np.ndarray) -> str:
        text = self.engine.transcribe(audio)
        if (text and self.corrector is not None
                and len(text.split()) >= self.llm_min_words):
            text = self.corrector.correct(text)
        return text


class RemoteBackend:
    def __init__(self, cfg: dict):
        self.url = cfg["remote_url"].rstrip("/")
        self.token = cfg.get("remote_token", "")
        self.device = "remote"

    def warmup(self) -> None:
        try:
            with urllib.request.urlopen(self.url + "/health", timeout=5) as r:
                info = json.loads(r.read().decode("utf-8"))
                print(f"[remote] serveur OK (device {info.get('device')})")
        except Exception as exc:  # noqa: BLE001
            print(f"[remote] serveur injoignable pour l'instant ({exc!r})")

    def process(self, audio: np.ndarray) -> str:
        data = np.ascontiguousarray(audio, dtype=np.float32).tobytes()
        req = urllib.request.Request(
            self.url + "/transcribe", data=data,
            headers={
                "Content-Type": "application/octet-stream",
                "X-Token": self.token,
            },
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read().decode("utf-8"))
        return resp.get("text", "")


def make_backend(cfg: dict, vocabulary: list[str]):
    if cfg.get("backend") == "remote":
        return RemoteBackend(cfg)
    return LocalBackend(cfg, vocabulary)
