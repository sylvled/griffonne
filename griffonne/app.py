"""Contrôleur Griffonne : raccourci global (toggle), capture micro, traitement
via un backend (local ou distant), auto-collage et apprentissage du vocabulaire.

Utilisable en mode console (`python -m griffonne.app`) ou piloté par le tray."""
import threading
import time

from pynput import keyboard as pk

from . import config, hotkeys, vocab_builder, win
from .audio import Recorder
from .backend import make_backend
from .devices import resolve_mic
from .output import output_text
from .sound import play_cue

# états
LOADING, IDLE, RECORDING, BUSY, DISABLED = (
    "loading", "idle", "recording", "busy", "disabled")


class Griffonne:
    def __init__(self, cfg: dict | None = None, on_status=None):
        self.cfg = cfg or config.load()
        self.on_status = on_status or (lambda s: None)
        self.recorder: Recorder | None = None
        self.backend = None
        self.vocabulary: list[str] = []
        self.state = LOADING
        self._listener: pk.GlobalHotKeys | None = None
        self._target_hwnd = None  # fenêtre cible mémorisée à l'arrêt de l'écoute
        self._target_ctrl = None  # contrôle (champ) qui avait le focus dedans
        self._quit = threading.Event()

    # ------------------------------------------------------------------ utils
    def _set_state(self, s: str) -> None:
        self.state = s
        try:
            self.on_status(s)
        except Exception:  # noqa: BLE001
            pass

    def _hotkey_vks(self) -> list[int]:
        """Codes VK des touches non-modificatrices du raccourci (les modificateurs
        sont déjà surveillés par win.wait_keys_released)."""
        return hotkeys.vk_codes(self.cfg["hotkey"])

    def _log_mic(self, idx) -> None:
        """Trace le micro réellement utilisé (le réglage peut ne plus exister)."""
        try:
            from .devices import list_microphones, mic_label
            mics = list_microphones()
            if idx is None:
                dflt = next((m for m in mics if m["default"]), None)
                print("[griffonne] micro : défaut Windows"
                      + (f" → {mic_label(dflt)}" if dflt else ""))
            else:
                m = next((m for m in mics if m["index"] == idx), None)
                print(f"[griffonne] micro : {mic_label(m) if m else f'index {idx}'}")
            if self.cfg["mic_device"] and idx is None:
                print(f"[griffonne] ⚠️  micro configuré « {self.cfg['mic_device']} » "
                      "introuvable (déconnecté ?) — repli sur le défaut Windows")
        except Exception as exc:  # noqa: BLE001
            print(f"[griffonne] micro : (info indisponible : {exc!r})")

    def _cue(self, kind: str) -> None:
        if self.cfg["beep"]:
            play_cue(kind, self.cfg["beep_volume"])

    # ------------------------------------------------------------------ cycle
    def start(self) -> None:
        idx = resolve_mic(self.cfg["mic_device"])
        self.recorder = Recorder(device=idx)
        self._log_mic(idx)
        threading.Thread(target=self._load_backend, daemon=True).start()
        self._start_hotkeys()

    def _load_backend(self) -> None:
        self._set_state(LOADING)
        eng = self.cfg.get("engine", "whisper")
        desc = "Parakeet 0.6B" if eng == "parakeet" else f"Whisper {self.cfg['model']}"
        print(f"[griffonne] backend '{self.cfg['backend']}' — moteur {desc}...")
        t0 = time.time()
        self.vocabulary = vocab_builder.build(self.cfg)
        print(f"[griffonne] vocabulaire : {len(self.vocabulary)} termes")
        self.backend = make_backend(self.cfg, self.vocabulary)
        self.backend.warmup()
        hk = (hotkeys.pretty(self.cfg["hotkey"]) if self._listener is not None
              else "AUCUN (raccourci invalide, voir ci-dessus)")
        print(f"[griffonne] PRÊT en {time.time() - t0:.1f}s "
              f"(device {self.backend.device}) — raccourci : {hk}")
        self._set_state(DISABLED if not self.cfg["enabled"] else IDLE)

    def _build_listener(self, cfg: dict) -> pk.GlobalHotKeys:
        """Construit le listener (non démarré). Lève ValueError si un raccourci
        est invalide — AVANT de toucher au listener en place."""
        table = {hotkeys.to_pynput(cfg["hotkey"]): self._safe_toggle}
        # Raccourci « quitter » désactivé par défaut : un raccourci global qui
        # tue l'app silencieusement est un piège (voisin du raccourci dictée).
        quit_key = (cfg.get("quit_hotkey") or "").strip()
        if quit_key:
            table[hotkeys.to_pynput(quit_key)] = (
                lambda: self.shutdown("raccourci quitter"))
        return pk.GlobalHotKeys(table)

    def _start_hotkeys(self) -> bool:
        try:
            listener = self._build_listener(self.cfg)
        except ValueError as exc:
            print(f"[griffonne] ⚠️  raccourci invalide « {self.cfg['hotkey']} » "
                  f"({exc}) — AUCUN raccourci actif. Corrige-le dans Réglages.")
            self._listener = None
            return False
        listener.start()
        self._listener = listener
        return True

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
            # le chargement du LLM (~4 s à froid) se fait pendant qu'on parle
            if self.backend is not None and hasattr(self.backend, "preload"):
                self.backend.preload()
            self._cue("start")
            print("[griffonne] 🎙️  enregistrement...")
        elif self.state == RECORDING:
            # mémorise MAINTENANT la fenêtre visée ET le contrôle qui a le
            # focus dedans (corrects à l'instant où l'utilisateur arrête)
            self._target_hwnd = win.get_foreground_window()
            self._target_ctrl = win.get_focused_control(self._target_hwnd)
            self._set_state(BUSY)
            self._cue("stop")
            threading.Thread(target=self._finish, daemon=True).start()
        # LOADING / BUSY / DISABLED : on ignore

    def _finish(self) -> None:
        audio = self.recorder.stop()
        dur = len(audio) / self.recorder.sr
        from .engine import audio_is_usable
        why = audio_is_usable(audio, self.recorder.sr)
        if why:
            print(f"[griffonne] ⏭️  dictée ignorée : {why} ({dur:.1f}s)")
            self._set_state(IDLE if self.cfg["enabled"] else DISABLED)
            return
        print(f"[griffonne] ⏳ traitement ({dur:.1f}s d'audio)...")
        t0 = time.time()
        try:
            text = self.backend.process(audio)
        except Exception as exc:  # noqa: BLE001
            print(f"[griffonne] erreur : {exc!r}")
            self._set_state(IDLE)
            return
        print(f"[griffonne] ✅ ({time.time() - t0:.1f}s) : {text}")
        if text:
            if self.cfg["auto_paste"] and self._target_hwnd:
                # 1) les touches du raccourci doivent être relâchées, sinon
                #    le Ctrl+V part en Ctrl+Alt+V (chaîne rapide = course)
                released = win.wait_keys_released(self._hotkey_vks())
                # 2) fenêtre + contrôle d'origine remis au premier plan
                focused = win.focus_window(self._target_hwnd, self._target_ctrl)
                time.sleep(0.12)
                print(f"[griffonne] 📋 collage dans « {win.window_title(self._target_hwnd)} » "
                      f"(focus {'ok' if focused else 'ÉCHEC'}, touches "
                      f"{'relâchées' if released else 'ENCORE ENFONCÉES'})")
            output_text(text, self.cfg["auto_paste"])
            if self.cfg["backend"] == "local":  # apprentissage local
                vocab_builder.learn(text, self.cfg)
        self._set_state(IDLE if self.cfg["enabled"] else DISABLED)

    # --------------------------------------------------------------- contrôle
    def reload(self, new_cfg: dict) -> None:
        """Applique une nouvelle config (réglages) : on recharge tout.
        Les raccourcis sont validés AVANT d'arrêter l'ancien listener : un
        raccourci invalide ne doit jamais faire perdre le clavier."""
        for key in ("hotkey", "quit_hotkey"):
            combo = (new_cfg.get(key) or "").strip()
            if combo:
                ok, msg = hotkeys.validate(combo)
                if not ok:
                    print(f"[griffonne] ⚠️  réglage refusé, raccourci « {combo} » "
                          f"invalide : {msg}. L'ancien reste actif.")
                    raise ValueError(f"Raccourci « {combo} » invalide : {msg}")
        print("[griffonne] rechargement de la configuration...")
        if self._listener is not None:
            self._listener.stop()
        self.cfg = new_cfg
        self.backend = None
        self.start()

    def shutdown(self, reason: str = "demande") -> None:
        # toujours tracer la cause : un arrêt silencieux est indiagnosticable
        print(f"[griffonne] ARRÊT ({reason}) à "
              f"{time.strftime('%d/%m/%Y %H:%M:%S')}", flush=True)
        if self._listener is not None:
            self._listener.stop()
        self._quit.set()

    def run_console(self) -> None:
        """Mode console bloquant (run.bat)."""
        self.start()
        self._quit.wait()
        print("\n[griffonne] arrêt.")


def main() -> None:
    Griffonne().run_console()


if __name__ == "__main__":
    main()
