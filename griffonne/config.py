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

    # --- modes de dictée (mot déclencheur en début de dictée) ---
    # « Mail, préviens Paul que... » → le texte brut est RÉÉCRIT en message
    # structuré. Les autres dictées restent transcrites fidèlement.
    "modes_enabled": True,
    "modes": {
        "mail": {
            "triggers": ["mail", "e-mail", "email", "courriel", "mél"],
            "model": "",          # vide = même modèle que la correction
            "temperature": 0.2,  # souplesse rédactionnelle
            "prompt": "\n".join((
                "Tu rédiges un e-mail professionnel en français à partir de "
                "notes dictées à voix haute, brutes et désordonnées.",
                "RÈGLES :",
                "- Structure, dans cet ordre EXACT : (1) la toute première "
                "ligne est « Objet : ... » ; (2) une ligne vide ; (3) la "
                "salutation ; (4) le corps en paragraphes courts ; (5) une "
                "formule de politesse. Rien d'autre.",
                "- Ne signe pas et n'ajoute aucun espace réservé du type "
                "« [Votre Nom] » : termine par la formule de politesse.",
                "- N'INVENTE AUCUN FAIT : aucun nom, date, chiffre, montant ou "
                "engagement qui ne soit pas dans les notes. Si le destinataire "
                "n'est pas nommé, écris simplement « Bonjour, ».",
                "- Conserve TOUTES les informations des notes, sans en ajouter.",
                "- Vouvoiement par défaut ; tutoie seulement si les notes "
                "tutoient.",
                "- Style clair et courtois, phrases directes. Pas de markdown, "
                "pas d'astérisques.",
                "- Ne commente pas ton travail : réponds UNIQUEMENT par l'e-mail.",
            )),
        },
        # Variante rédactionnelle du mode « mail » : même structure, mais le
        # modèle est autorisé à passer du registre oral à l'écrit. À comparer
        # à l'usage avec « mail » — plus propre, mais il reformule davantage.
        "mail_soigne": {
            "triggers": ["mail soigné", "mail propre", "beau mail",
                         "e-mail soigné"],
            "model": "",
            "temperature": 0.2,
            "prompt": "\n".join((
                "Tu rédiges un e-mail professionnel en français à partir de "
                "notes dictées à voix haute, brutes et désordonnées.",
                "RÈGLES :",
                "- Structure, dans cet ordre EXACT : (1) la toute première "
                "ligne est « Objet : ... » ; (2) une ligne vide ; (3) la "
                "salutation ; (4) le corps en paragraphes courts ; (5) une "
                "formule de politesse. Rien d'autre.",
                "- Ne signe pas et n'ajoute aucun espace réservé du type "
                "« [Votre Nom] ».",
                "- RÈGLE DE FIDÉLITÉ, PRIORITAIRE SUR TOUTES LES AUTRES : "
                "chaque idée dictée doit se retrouver dans l'e-mail — en "
                "particulier les refus, réserves, conditions et regrets. Ne "
                "supprime, ne fusionne et ne résume JAMAIS une phrase porteuse "
                "d'information. N'ajoute aucune phrase d'introduction, question "
                "ou conclusion qui ne soit pas dictée.",
                "- Les notes sont dictées à l'oral. Tu es autorisé à faire "
                "SEULEMENT ces quatre retouches de forme : (a) supprimer les "
                "connecteurs oraux en début de phrase (« Et », « Et donc », "
                "« En fait », « Alors », « Du coup », « Voilà ») ; (b) supprimer "
                "une répétition immédiate (« de notre côté, côté X » → « Du côté "
                "X ») ; (c) corriger la grammaire et les accords ; (d) écrire "
                "« X est un Y » au lieu de « X, c'est un Y ». Rien d'autre.",
                "- Ces retouches changent la forme, jamais le fond : à part "
                "elles, reprends les phrases de la dictée telles quelles.",
                "- N'INVENTE AUCUN FAIT : aucun nom, date, chiffre ou "
                "engagement absent des notes. Si le destinataire n'est pas "
                "nommé, écris simplement « Bonjour, ».",
                "- Vouvoiement par défaut ; tutoie seulement si les notes "
                "tutoient. Pas de markdown.",
                "- Réponds UNIQUEMENT par l'e-mail.",
            )),
        },
        "message": {
            "triggers": ["message", "chat", "teams"],
            "model": "",
            "temperature": 0.2,  # souplesse rédactionnelle
            "prompt": "\n".join((
                "Tu rédiges un message court et direct, destiné à une messagerie "
                "professionnelle (Teams, Slack), à partir de notes dictées.",
                "RÈGLES :",
                "- Pas d'objet, pas de salutation cérémonieuse, pas de signature. "
                "Va droit au but.",
                "- Ton courtois et naturel, phrases brèves. Deux ou trois "
                "phrases suffisent le plus souvent.",
                "- Passe du registre oral à l'écrit : supprime les connecteurs "
                "de l'oral en début de phrase (« Et », « Du coup », « En "
                "fait »), les répétitions et les fragments inachevés ; corrige "
                "la grammaire. Cela ne retire aucune information.",
                "- N'invente aucun fait ; conserve toutes les informations.",
                "- Pas de markdown ni d'astérisques.",
                "- Réponds UNIQUEMENT par le message.",
            )),
        },
        "note": {
            "triggers": ["note", "compte rendu", "notes"],
            "model": "",
            "temperature": 0.1,  # fidélité stricte
            "prompt": "\n".join((
                "Tu mets en forme des notes dictées en un compte rendu clair en "
                "français.",
                "RÈGLES :",
                "- Structure : un titre court en première ligne, puis des puces "
                "commençant par « - », regroupées par thème.",
                "- Si des actions à faire apparaissent, termine par une section "
                "« À faire : » avec une puce par action.",
                "- N'invente aucun fait ; conserve TOUTES les informations.",
                "- Pas d'astérisques ni de numérotation inutile.",
                "- Réponds UNIQUEMENT par le compte rendu.",
            )),
        },
        "resume": {
            "triggers": ["résumé", "resume", "synthèse"],
            "model": "",
            "temperature": 0.1,  # fidélité stricte
            "prompt": "\n".join((
                "Tu résumes en français des propos dictés.",
                "RÈGLES :",
                "- Ne garde que l'essentiel : points clés, décisions, chiffres.",
                "- Trois à six puces « - » au maximum, une idée par puce.",
                "- N'ajoute AUCUNE information absente des propos.",
                "- Pas d'introduction ni de conclusion : réponds UNIQUEMENT par "
                "le résumé.",
            )),
        },
        "anglais": {
            "triggers": ["anglais", "english", "traduction"],
            "model": "",
            "temperature": 0.1,  # fidélité stricte
            "prompt": "\n".join((
                "You translate dictated French notes into clear, professional "
                "English.",
                "RULES:",
                "- Keep the meaning and ALL the information. Add nothing.",
                "- Keep technical terms, product names and proper nouns "
                "unchanged.",
                "- Natural, idiomatic English; no markdown.",
                "- Answer with the translation ONLY.",
            )),
        },
        "ticket": {
            "triggers": ["ticket", "incident", "bug"],
            "model": "",
            "temperature": 0.1,  # fidélité stricte
            "prompt": "\n".join((
                "Tu rédiges un signalement d'incident clair en français à partir "
                "de notes dictées.",
                "RÈGLES :",
                "- Première ligne : « Titre : ... » (une phrase courte et "
                "factuelle).",
                "- Puis UNIQUEMENT les sections que la dictée renseigne "
                "explicitement, parmi : « Contexte », « Problème constaté », "
                "« Étapes pour reproduire », « Impact ».",
                "- INTERDIT ABSOLU d'inventer : n'ajoute jamais une étape, une "
                "manipulation, un message d'erreur, une cause ou une "
                "conséquence qui n'a pas été dictée. En particulier, n'écris "
                "une section « Étapes pour reproduire » QUE si la dictée décrit "
                "des manipulations précises ; sinon, omets-la entièrement.",
                "- Chaque phrase doit correspondre à une information réellement "
                "présente dans la dictée. Aucune supposition sur l'usage du "
                "système, aucune extrapolation.",
                "- Ne signale JAMAIS qu'une information est absente ou non "
                "décrite : supprime purement et simplement la section "
                "concernée, sans la mentionner.",
                "- Conserve les termes techniques et noms propres à l'identique.",
                "- Réponds UNIQUEMENT par le signalement.",
            )),
        },
    },

    # --- correction LLM locale (Ollama) ---
    "llm_correct": True,          # relecture/correction par LLM local
    "llm_model": "qwen2.5:3b",    # modèle Ollama (petit = rapide)
    "llm_mode": "conservative",   # "conservative" ou "light" (nettoyage style)
    "llm_min_words": 2,           # n'appelle pas le LLM en dessous (trop court)
    # IMPORTANT : 127.0.0.1 et NON localhost. Sous Windows, « localhost » tente
    # d'abord IPv6 (::1) alors qu'Ollama n'écoute qu'en IPv4 -> ~2 s perdues
    # par appel avant le repli. Mesuré : 2,36 s -> 0,16 s.
    "ollama_url": "http://127.0.0.1:11434",
    "llm_keep_alive": -1,         # -1 = modèle résident tant qu'Ollama tourne.
                                  # Décharger n'apporte rien : Ollama évince
                                  # déjà le modèle si un autre en a besoin.

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
            user = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cfg
        for key, value in user.items():
            # Fusion d'un niveau pour les dictionnaires (« modes »,
            # « replacements ») : sans cela, une config existante masquerait
            # définitivement tout nouveau mode livré avec l'application.
            # Les réglages de l'utilisateur restent prioritaires.
            if isinstance(value, dict) and isinstance(cfg.get(key), dict):
                merged = dict(cfg[key])
                merged.update(value)
                cfg[key] = merged
            else:
                cfg[key] = value
    return cfg


def save(cfg: dict) -> None:
    # ne persiste que les clés connues, dans l'ordre des défauts
    clean = {k: cfg.get(k, v) for k, v in DEFAULTS.items()}
    CONFIG_PATH.write_text(
        json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8"
    )
