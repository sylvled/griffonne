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


_API_INFO = {
    # nom PortAudio -> (libellé court, rang de préférence, remarque)
    "Windows WASAPI":     ("WASAPI", 0, "natif, sans rééchantillonnage — recommandé"),
    "Windows WDM-KS":     ("WDM-KS", 1, "accès exclusif au périphérique, peut gêner les autres apps"),
    "Windows DirectSound": ("DirectSound", 2, "même micro, rééchantillonné par Windows"),
    "MME":                ("MME", 3, "même micro, rééchantillonné par Windows (API ancienne)"),
}


def _clean_name(raw: str) -> str:
    """Rend lisibles les noms de pilotes Bluetooth Hands-Free :
    'Casque (@System32/drivers/bthhfenum.sys,#2;%1 Hands-Free%0 ;(ACCENTUM))'
;(ACCENTUM))'
    -> 'Casque ACCENTUM (Bluetooth Hands-Free)'."""
    import re
    m = re.search(r"bthhfenum.*?\(([^()]+)\)\)?\s*$", raw, re.S)
    if m:
        base = raw.split("(")[0].strip() or "Micro"
        return f"{base} {m.group(1).strip()} (Bluetooth Hands-Free)"
    return " ".join(raw.split())


def list_microphones() -> list[dict]:
    """Périphériques d'entrée, enrichis : API Windows, débit natif, doublons
    du même micro repérés, entrée recommandée marquée.

    Un même micro apparaît une fois par API (MME, DirectSound, WASAPI, WDM-KS) :
    le signal est identique, seuls latence et rééchantillonnage diffèrent."""
    import sounddevice as sd
    try:
        default_in = sd.default.device[0]
    except Exception:  # noqa: BLE001
        default_in = None
    apis = sd.query_hostapis()
    out = []
    for i, d in enumerate(sd.query_devices()):
        if d.get("max_input_channels", 0) <= 0:
            continue
        api_raw = apis[d["hostapi"]]["name"]
        short, rank, note = _API_INFO.get(api_raw, (api_raw, 9, ""))
        clean = _clean_name(d["name"])
        out.append({
            "index": i, "name": d["name"], "clean": clean, "api": short,
            "rank": rank, "note": note, "samplerate": int(d["default_samplerate"]),
            "channels": d["max_input_channels"], "default": (i == default_in),
        })
    # --- regroupement des doublons (même micro vu par plusieurs API) ---
    # MME tronque les noms à 31 caractères et WDM-KS utilise le nom du pilote :
    # on compare des clés alphanumériques par préfixe.
    import re
    def key(m):
        return re.sub(r"[^a-z0-9]", "", m["clean"].lower())
    groups: list[list[dict]] = []
    for m in sorted(out, key=lambda m: len(key(m))):
        k = key(m)
        for g in groups:
            gk = key(g[0])
            if k.startswith(gk) or gk.startswith(k):
                g.append(m); break
        else:
            groups.append([m])
    ALIAS = ("mappeur de sons", "sound mapper", "pilote de capture audio principal",
             "primary sound capture")
    for g in groups:
        g.sort(key=lambda m: m["rank"])
        apis = {m["api"] for m in g}
        ghost = apis == {"WDM-KS"}   # visible seulement par l'énumérateur noyau
        for i, m in enumerate(g):
            m["alias"] = any(a in m["clean"].lower() for a in ALIAS)
            m["recommended"] = (i == 0 and not ghost and not m["alias"])
            m["ghost"] = ghost and not m["alias"]
            m["group"] = key(g[0])
            m["spec"] = f"{m['clean']}|{m['api']}"   # identifiant stable (≠ index)
    # groupes : d'abord les micros réellement utilisables, puis les fantômes
    out.sort(key=lambda m: (m["ghost"], m["group"], m["rank"]))
    return out


def mic_label(m: dict) -> str:
    """Libellé affiché dans les réglages."""
    khz = f"{m['samplerate']/1000:g} kHz"
    parts = [m["clean"], m["api"], khz]
    if m.get("ghost"):
        parts.append("non connecté ?")
    if m.get("alias"):
        parts.append("alias du micro par défaut Windows")
    label = " · ".join(parts)
    if m.get("recommended"):
        label += " ★ recommandé"
    elif m["note"] and not m.get("ghost"):
        label += f" — {m['note']}"
    if m["default"]:
        label += " [défaut Windows]"
    return label


def resolve_mic(mic_device) -> int | None:
    """Résout le réglage `mic_device` en index sounddevice, ou None (défaut).
    Accepte : un index (fragile : change quand un appareil se (dé)connecte),
    un identifiant stable « nom|API » (produit par les réglages), ou une
    sous-chaîne du nom (on prend alors la meilleure API disponible)."""
    if mic_device is None or mic_device == "":
        return None
    if isinstance(mic_device, int):
        return mic_device
    spec = str(mic_device)
    if spec.isdigit():
        return int(spec)
    mics = list_microphones()
    if "|" in spec:
        name, api = spec.rsplit("|", 1)
        for m in mics:                       # exactement ce micro par cette API
            if m["clean"] == name and m["api"] == api:
                return m["index"]
        for m in mics:                       # même micro, autre API (meilleure)
            if m["clean"] == name and not m["ghost"]:
                return m["index"]
        spec = name
    needle = spec.lower()
    hits = [m for m in mics if needle in m["clean"].lower() or needle in m["name"].lower()]
    hits = [m for m in hits if not m["ghost"]] or hits
    if hits:
        return sorted(hits, key=lambda m: m["rank"])[0]["index"]
    return None
