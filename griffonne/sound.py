"""Petits signaux sonores (début/fin d'enregistrement) à volume réglable.
Génère une tonalité via sounddevice plutôt que winsound.Beep (volume fixe)."""
import numpy as np
import sounddevice as sd

SR = 44100


def play_cue(kind: str, volume: float = 0.2) -> None:
    if volume <= 0:
        return
    freq = 660 if kind == "start" else 380  # aigu = début, grave = fin
    vol = volume if kind == "start" else volume * 0.8  # fin un peu plus douce
    dur = 0.09
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    wave = (np.sin(2 * np.pi * freq * t) * vol).astype(np.float32)
    # fondu de 6 ms en entrée/sortie pour éviter les "clics"
    fade = int(SR * 0.006)
    if fade and len(wave) > 2 * fade:
        wave[:fade] *= np.linspace(0, 1, fade)
        wave[-fade:] *= np.linspace(1, 0, fade)
    try:
        sd.play(wave, SR)  # non bloquant
    except Exception:  # noqa: BLE001 — un bip raté ne doit jamais planter l'app
        pass
