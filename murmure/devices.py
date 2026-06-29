"""Détection matérielle : GPU CUDA disponible, et liste des micros."""
import sys
from pathlib import Path


def cuda_available() -> bool:
    """Vrai si ctranslate2 voit au moins un GPU CUDA utilisable."""
    if sys.platform == "win32":
        base = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
        import os
        for sub in ("cublas/bin", "cudnn/bin"):
            p = base / sub
            if p.is_dir():
                try:
                    os.add_dll_directory(str(p))
                except OSError:
                    pass
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def resolve_device(device: str, compute_type: str) -> tuple[str, str]:
    """Transforme ('auto', 'auto') en valeurs concrètes selon le matériel."""
    if device == "auto":
        device = "cuda" if cuda_available() else "cpu"
    if compute_type == "auto":
        compute_type = "float16" if device == "cuda" else "int8"
    return device, compute_type


def list_microphones() -> list[dict]:
    """Renvoie [{'index', 'name', 'default'}] des périphériques d'entrée."""
    import sounddevice as sd
    out = []
    try:
        default_in = sd.default.device[0]
    except Exception:
        default_in = None
    for i, d in enumerate(sd.query_devices()):
        if d.get("max_input_channels", 0) > 0:
            out.append({
                "index": i,
                "name": d["name"],
                "default": (i == default_in),
            })
    return out


def resolve_mic(mic_device) -> int | None:
    """mic_device peut être un index (int) ou une sous-chaîne du nom.
    Renvoie un index de périphérique, ou None pour le défaut système."""
    if mic_device is None or mic_device == "":
        return None
    if isinstance(mic_device, int):
        return mic_device
    if isinstance(mic_device, str) and mic_device.isdigit():
        return int(mic_device)
    needle = str(mic_device).lower()
    for d in list_microphones():
        if needle in d["name"].lower():
            return d["index"]
    return None
