"""Contrôleur Murmure : raccourci global (toggle), capture micro, traitement
via un backend (local ou distant), auto-collage et apprentissage du vocabulaire.

Utilisable en mode console (`python -m murmure.app`) ou piloté par le tray."""
import threading
import time

from pynput import keyboard as pk

from . import config, vocab_builder, win
from .audio import Recorder
from .backend import make_backend
from .devices import resolve_mic
from .output import output_text
from .sound import play_cue

# états
LOADING, IDLE, RECORDING, BUSY, DISABLED = (
    "loading", "idle", "recording", "busy", "disabled")


def _to_pynput_hotkey(combo: str) -> str:
    """'ctrl+alt+space' -> '<ctrl>+<alt>+<space>' (format pynput)."""
    parts = []
    for p in combo.lower().split("+"):
        p = p.strip()
        parts.append(p if len(p) == 1 else f"<{p}>")
    return "+".join(parts)


class Murmure:
    def __init__(self, cfg: dict | None = None, on_status=None):
        self.cfg = cfg or config.load()
        self.on_status = on_status or (lambda s: None)
        self.recorder: Recorder | None = None
        self.backend = None
        self.vocabulary: list[str] = []
        self.state = LOADING
        self._listener: pk.GlobalHotKeys | None = None
        self._target_hwnd = None  # fenêtre cible mémorisée à l'arrêt de l'écoute
        self._quit = threading.Event()

    # ------------------------------------------------------------------ utils
    def _set_state(self, s: str) -> None:
        self.state = s
        try:
            self.on_status(s)
        except Exception:  # noqa: BLE001
            pass

    def _cue(self, kind: str) -> None:
        if self.cfg["beep"]:
            play_cue(kind, self.cfg["beep_volume"])

    # ------------------------------------------------------------------ cycle
    def start(self) -> None:
        self.recorder = Recorder(device=resolve_mic(self.cfg["mic_device"]))
        threading.Thread(target=self._load_backend, daemon=True).start()
        self._start_hotkeys()

    def _load_backend(self) -> None:
        self._set_state(LOADING)
        eng = self.cfg.get("engine", "whisper")
        desc = "Parakeet 0.6B" if eng == "parakeet" else f"Whisper {self.cfg['model']}"
        print(f"[murmure] backend '{self.cfg['backend']}' — moteur {desc}...")
        t0 = time.time()
        self.vocabulary = vocab_builder.build(self.cfg)
        print(f"[murmure] vocabulaire : {len(self.vocabulary)} termes")
        self.backend = make_backend(self.cfg, self.vocabulary)
        self.backend.warmup()
        print(f"[murmure] PRÊT en {time.time() - t0:.1f}s "
              f"(device {self.backend.device}) — raccourci {self.cfg['hotkey']}")
        self._set_state(DISABLED if not self.cfg["enabled"] else IDLE)

    def _start_hotkeys(self) -> None:
        hotkeys = {_to_pynput_hotkey(self.cfg["hotkey"]): self._safe_toggle}
        # Raccourci « quitter » désactivé par défaut : un raccourci global qui
        # tue l'app silencieusement est un piège (voisin du raccourci dictée).
        quit_key = (self.cfg.get("quit_hotkey") or "").strip()
        if quit_key:
            hotkeys[_to_pynput_hotkey(quit_key)] = (
                lambda: self.shutdown("raccourci quitter"))
        self._listener = pk.GlobalHotKeys(hotkeys)
        self._listener.start()

    def _safe_toggle(self) -> None:
        threading.Thread(target=self.toggle, daemon=True).start()

    def set_enabled(self, enabled: bool) -> None:
        self.cfg["enabled"] = enabled
        if not enabled and self.state == RECORDING:
            self.recorder.stop()
        if self.backend is not None:
            self._set_state(IDLE if enabled else DISABLED)

    # --------------------------------------------------------------- dictée
    def toggle(self) -> None:
        if not self.cfg["enabled"] or self.backend is None:
            return
        if self.state == IDLE:
            self._set_state(RECORDING)
            self.recorder.start()
            self._cue("start")
            print("[murmure] 🎙️  enregistrement...")
        elif self.state == RECORDING:
            # mémorise MAINTENANT la fenêtre visée (le focus est correct à
            # l'instant où l'utilisateur arrête l'écoute)
            self._target_hwnd = win.get_foreground_window()
            self._set_state(BUSY)
            self._cue("stop")
            threading.Thread(target=self._finish, daemon=True).start()
        # LOADING / BUSY / DISABLED : on ignore

    def _finish(self) -> None:
        audio = self.recorder.stop()
        dur = len(audio) / self.recorder.sr
        print(f"[murmure] ⏳ traitement ({dur:.1f}s d'audio)...")
        t0 = time.time()
        try:
            text = self.backend.process(audio)
        except Exception as exc:  # noqa: BLE001
            print(f"[murmure] erreur : {exc!r}")
            self._set_state(IDLE)
            return
        print(f"[murmure] ✅ ({time.time() - t0:.1f}s) : {text}")
        if text:
            if self.cfg["auto_paste"] and self._target_hwnd:
                win.focus_window(self._target_hwnd)  # recible la bonne fenêtre
                time.sleep(0.12)
            output_text(text, self.cfg["auto_paste"])
            if self.cfg["backend"] == "local":  # apprentissage local
                vocab_builder.learn(text, self.cfg)
        self._set_state(IDLE if self.cfg["enabled"] else DISABLED)

    # --------------------------------------------------------------- contrôle
    def reload(self, new_cfg: dict) -> None:
        """Applique une nouvelle config (réglages) : on recharge tout."""
        print("[murmure] rechargement de la configuration...")
        if self._listener is not None:
            self._listener.stop()
        self.cfg = new_cfg
        self.backend = None
        self.start()

    def shutdown(self, reason: str = "demande") -> None:
        # toujours tracer la cause : un arrêt silencieux est indiagnosticable
        print(f"[murmure] ARRÊT ({reason}) à "
              f"{time.strftime('%d/%m/%Y %H:%M:%S')}", flush=True)
        if self._listener is not None:
            self._listener.stop()
        self._quit.set()

    def run_console(self) -> None:
        """Mode console bloquant (run.bat)."""
        self.start()
        self._quit.wait()
        print("\n[murmure] arrêt.")


def main() -> None:
    Murmure().run_console()


if __name__ == "__main__":
    main()
