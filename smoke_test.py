"""Test de sanité : charge le moteur sur GPU et transcrit 1 s de silence.
Valide le chargement des DLL CUDA/cuDNN (le point le plus fragile)."""
import time

import numpy as np

from murmure.engine import LocalEngine

print("Chargement du moteur (cuda / large-v3-turbo)...")
t0 = time.time()
eng = LocalEngine(model="large-v3-turbo", device="cuda",
                  compute_type="float16", language="fr")
print(f"OK en {time.time() - t0:.1f}s — device réel : {eng.device}")

silence = np.zeros(16000, dtype=np.float32)  # 1 s
print("Transcription d'1 s de silence (doit renvoyer une chaîne, sans crash)...")
t0 = time.time()
txt = eng.transcribe(silence)
print(f"Résultat : {txt!r}  ({time.time() - t0:.2f}s)")
print("=> GPU OK." if eng.device == "cuda" else "=> Tourne en CPU (repli).")
