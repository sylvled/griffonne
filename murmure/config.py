"""Chargement / sauvegarde de la configuration utilisateur (JSON)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"

DEFAULTS = {
    # --- état ---
    "enabled": True,             # dictée active (pilotable depuis le tray)

    # --- moteur ---
    "backend": "local",          # "local" | "remote" | "auto" (distant si joignable)
    # "whisper" (défaut, précision max avec amorce vocabulaire) ou
    # "parakeet" (NVIDIA Parakeet 0.6B : ~0,4 s sur CPU, ~0,2 s en CUDA ;
    # langue auto-détectée). Basculable à tout moment (Réglages ou menu tray).
    "engine": "whisper",
    "model": "large-v3-turbo",   # (Whisper) large-v3-turbo | large-v3 | small ...
    "device": "auto",            # "auto" | "cuda" | "cpu" (mode dégradé)
    "compute_type": "auto",      # "auto" | float16 (gpu) | int8 (cpu)
    "language": "fr",            # code langue, ou null pour auto-détection

    # Phrase d'amorce de base (le vocabulaire est ajouté automatiquement).
    "initial_prompt": "Dictée vocale en français.",

    # Vocabulaire « graine » (toujours présent). Le reste se construit tout
    # seul (cf. vocab_auto / vocab_learn). Orthographe EXACTE des termes.
    "vocabulary": [
        "reconnaissance vocale", "Whisper", "Ollama", "GitHub", "Python",
        "Windows", "Linux", "PDF", "API", "VPN",
    ],
    # Construction automatique du vocabulaire.
    "vocab_auto": True,          # utilise le vocabulaire construit (sinon graine seule)
    "vocab_learn": True,         # APPREND les termes au fil des dictées (principal)
    "vocab_harvest": False,      # récolte aussi dans des fichiers prose (opt-in)
    "vocab_folders": [],         # dossiers à scanner (vide = défauts détectés)
    "vocab_min_count": 3,        # fréquence min. pour retenir un terme harvesté
    "vocab_max_terms": 400,      # plafond (garde l'amorce Whisper raisonnable)

    # Corrections déterministes pour les erreurs NON phonétiques que le LLM ne
    # peut pas deviner (filet de sécurité, insensible à la casse).
    "replacements": {
        "attitude vocale": "reconnaissance vocale",
    },

    # --- activation ---
    "hotkey": "ctrl+alt+m",      # raccourci global (toggle). PAS ctrl+alt+space :
                                 # conflit avec la barre de commande Claude Desktop.
    # Vide = désactivé (recommandé). Un raccourci global « quitter » se
    # déclenche trop facilement et arrête l'app sans prévenir.
    # Pour quitter : menu de l'icône « Quitter », ou Ctrl+C en mode console.
    "quit_hotkey": "",

    # --- entrée / sortie ---
    "mic_device": None,          # index/sous-chaîne du micro, ou null = défaut
    "auto_paste": True,          # colle directement dans le champ actif
    "beep": True,                # bip sonore début/fin
    "beep_volume": 0.05,         # volume des bips (0.0 = muet, 1.0 = max)
    "clean_fillers": True,       # supprime hésitations (euh, heu...) et bégaiements

    # --- correction LLM locale (Ollama) ---
    "llm_correct": True,          # relecture/correction par LLM local
    "llm_model": "qwen2.5:3b",    # modèle Ollama (petit = rapide)
    "llm_mode": "conservative",   # "conservative" ou "light" (nettoyage style)
    "llm_min_words": 2,           # n'appelle pas le LLM en dessous (trop court)
    # IMPORTANT : 127.0.0.1 et NON localhost. Sous Windows, « localhost » tente
    # d'abord IPv6 (::1) alors qu'Ollama n'écoute qu'en IPv4 -> ~2 s perdues
    # par appel avant le repli. Mesuré : 2,36 s -> 0,16 s.
    "ollama_url": "http://127.0.0.1:11434",
    "llm_keep_alive": "30m",      # garde le modèle en VRAM (évite les rechargements)

    # --- mode distant ---
    # CLIENT : où joindre le serveur de transcription.
    "remote_url": "http://127.0.0.1:8765",
    "remote_token": "",          # jeton partagé (obligatoire si exposé au réseau)
    # SERVEUR : interface/port d'écoute.
    "server_host": "0.0.0.0",
    "server_port": 8765,
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def save(cfg: dict) -> None:
    # ne persiste que les clés connues, dans l'ordre des défauts
    clean = {k: cfg.get(k, v) for k, v in DEFAULTS.items()}
    CONFIG_PATH.write_text(
        json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8"
    )
