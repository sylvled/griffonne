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
            # La consigne de langue est énoncée deux fois, dont la dernière en
            # position finale : un modèle 3B nourri d'un message français
            # répondait sinon en français une fois sur trois (mesuré).
            "prompt": "\n".join((
                "You are a French-to-English translator.",
                "The user message is in French. Your reply MUST be in English.",
                "RULES:",
                "- Translate everything. Keep the meaning and ALL the "
                "information. Add nothing.",
                "- Keep technical terms, product names and proper nouns "
                "unchanged.",
                # Sans cette règle, « 22h » devenait « 8 PM » : le modèle se
                # trompe dans la conversion, et une heure fausse est pire
                # qu'une heure au format inhabituel.
                "- Keep times in 24-hour format (22h -> 22:00). Never convert "
                "to AM/PM.",
                "- Dictated French is colloquial. Translate the intended "
                "meaning, not word for word: « a lâché », « est tombé », "
                "« a planté » = failed / went down.",
                "- Natural, idiomatic English; no markdown, no preamble.",
                "- Never reply in French. Output English only.",
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


# Empreintes SHA-256 des prompts de modes livrés par une version ANTÉRIEURE.
#
# Pourquoi : jusqu'ici config.json persistait tous les défauts, donc il a figé
# les prompts tels qu'ils étaient à la première sauvegarde. Une copie périmée
# d'un défaut livré est indiscernable d'une personnalisation voulue — sauf si
# on sait reconnaître ce qu'on a livré. Un prompt dont l'empreinte est ici est
# effacé au chargement : le défaut courant reprend la main. Un prompt écrit par
# l'utilisateur ne peut pas figurer dans cette liste, donc il n'est jamais
# perdu.
#
# À l'avenir : `save()` ne persiste plus que les écarts, donc les prompts ne
# sont plus stockés du tout et cette liste n'a plus à grandir. Elle ne sert
# qu'à rattraper les fichiers déjà écrits.
_PROMPTS_SUPPLANTES = {
    # mode « mail » : version contenant les règles « registre oral → écrit ».
    # Retirée car le modèle 3B y perdait du contenu — il résumait au lieu de
    # reformuler, et une phrase entière de la dictée pouvait disparaître.
    "85bb5be8d96b3e58c0c6f7a78cafa33a09d08eeed40945198f473d77b77418a6",
    # mode « anglais » : version qui ne disait la langue de sortie qu'une fois.
    # Le modèle répondait en français environ une fois sur trois.
    "2e761a2e463cb7aa0b8b505a37d2c372a6d3c69538bfd10bce2849010c17aeff",
}


def _drop_superseded_prompts(user: dict) -> dict:
    """Retire des modes stockés les prompts que nous avons nous-mêmes livrés
    dans une version antérieure (voir _PROMPTS_SUPPLANTES)."""
    modes = user.get("modes")
    if not isinstance(modes, dict):
        return user
    import hashlib
    out = dict(user)
    nettoyes = {}
    for name, spec in modes.items():
        if not isinstance(spec, dict) or "prompt" not in spec:
            nettoyes[name] = spec
            continue
        digest = hashlib.sha256(
            str(spec["prompt"]).encode("utf-8")).hexdigest()
        if digest in _PROMPTS_SUPPLANTES:
            spec = {k: v for k, v in spec.items() if k != "prompt"}
            print(f"[config] mode « {name} » : prompt obsolète remplacé "
                  "par la version livrée")
        if spec:
            nettoyes[name] = spec
    out["modes"] = nettoyes
    return out


def _merge(base: dict, user: dict) -> dict:
    """Superpose `user` sur `base`, en descendant dans les dictionnaires.

    Récursif, et non pas à un seul niveau : un mode dont l'utilisateur n'a
    changé que la température doit conserver le prompt livré. Une fusion
    plate remplacerait le mode entier et gèlerait son prompt."""
    out = dict(base)
    for key, value in user.items():
        current = out.get(key)
        if isinstance(value, dict) and isinstance(current, dict):
            out[key] = _merge(current, value)
        elif isinstance(current, dict) and key in base:
            # Édition manuelle malformée : remplacer un dictionnaire par un
            # scalaire ferait planter le code qui l'itère (« modes » devenu
            # une chaîne = plus aucune dictée, avec une erreur incompréhensible).
            # On garde le défaut et on le dit.
            print(f"[config] « {key} » doit être un objet JSON, pas "
                  f"{type(value).__name__} — valeur ignorée")
        else:
            out[key] = value
    return out


def _overrides(cfg: dict, defaults: dict) -> dict:
    """Ne retient de `cfg` que ce qui s'écarte de `defaults`.

    Pourquoi ne pas tout persister : config.json figerait alors les prompts
    des modes de dictée tels qu'ils étaient à la première sauvegarde, et
    aucune de leurs corrections ultérieures n'atteindrait l'utilisateur.
    En ne stockant que les écarts, un réglage qu'il n'a pas touché continue
    de suivre la valeur livrée.

    Les clés absentes des défauts sont conservées : ce sont ses propres
    ajouts (corrections de vocabulaire, mode personnalisé), pas du bruit."""
    out: dict = {}
    for key, value in cfg.items():
        if key not in defaults:
            out[key] = value
            continue
        dflt = defaults[key]
        if isinstance(value, dict) and isinstance(dflt, dict):
            sub = _overrides(value, dflt)
            if sub:
                out[key] = sub
        elif value != dflt:
            out[key] = value
    return out


def load() -> dict:
    cfg = dict(DEFAULTS)
    if not CONFIG_PATH.exists():
        return cfg
    try:
        user = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return cfg
    if not isinstance(user, dict):
        return cfg
    user = _drop_superseded_prompts(user)
    cfg = _merge(cfg, user)
    # Migration des fichiers écrits par une version antérieure, qui
    # persistaient tous les défauts : on réécrit en ne gardant que les
    # écarts, sinon les prompts livrés restent masqués pour toujours.
    # Jamais bloquant : un disque en lecture seule ne doit pas empêcher
    # l'application de démarrer.
    pruned = _overrides(cfg, DEFAULTS)
    if pruned != user:
        try:
            _write(pruned)
        except OSError as exc:
            print(f"[config] migration impossible ({exc!r}) — sans conséquence")
    return cfg


def _write(data: dict) -> None:
    CONFIG_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def save(cfg: dict) -> None:
    _write(_overrides(cfg, DEFAULTS))
