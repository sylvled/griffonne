"""Murmure - dictée vocale locale (équivalent SuperWhisper, gratuit)."""
import sys as _sys

__version__ = "1.0.0"

# Robustesse encodage : la console Windows (cp1252) plante sur les emojis et
# accents. On force l'UTF-8 en sortie, sans jamais lever d'exception.
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
