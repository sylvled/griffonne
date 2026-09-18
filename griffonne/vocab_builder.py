"""Construction AUTOMATIQUE du vocabulaire (zéro saisie manuelle).

Trois sources fusionnées :
  1. graine  : la liste `vocabulary` de la config (toujours conservée) ;
  2. récolte : termes techniques/noms propres extraits de tes fichiers ;
  3. appris  : termes vus dans tes dictées corrigées, accumulés au fil du temps.

Le résultat est mis en cache dans `vocabulary.json` (géré par le programme,
pas à éditer à la main)."""
import re
import time
from collections import Counter
from pathlib import Path

from .config import ROOT

CACHE = ROOT / "vocabulary.json"

# extensions texte à scanner : PROSE uniquement (les fichiers de code
# génèrent surtout des identifiants parasites, inutiles en dictée).
_TEXT_EXT = {".md", ".markdown", ".txt", ".rst", ".org"}
# dossiers ignorés
_SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__",
              ".cache", "dist", "build", ".idea", ".vscode", "site-packages"}

# acronymes en majuscules (NASA, GPU, HTML...) — 3 lettres minimum : les
# tokens de 2 lettres (EN, ST, CI...) sont trop souvent des mots courants
_ACRONYM = re.compile(r"\b[A-Z]{3,6}\b")
# identifiants en casse mixte (GitHub, PostgreSQL, iPhone, macOS...)
_MIXED = re.compile(r"\b(?:[A-Z]{2,}[a-z]\w*|[a-z]+[A-Z]\w*|[A-Z][a-z]+[A-Z]\w*)\b")

# bruit fréquent à exclure
_STOP = {
    "TODO", "FIXME", "NOTE", "XXX", "HACK", "BUG", "WARNING", "ERROR", "INFO",
    "DEBUG", "TRUE", "FALSE", "NULL", "NONE", "AND", "OR", "NOT", "THE", "FOR",
    "HTTP", "HTTPS", "HTML", "JSON", "YAML", "CSV", "XML", "URL", "URI", "API",
    "GET", "POST", "PUT", "ID", "OK", "UTF", "ASCII", "PEP", "UTC", "ISO",
}

# mots courants qui peuvent apparaître en majuscules dans une dictée : jamais
# appris comme vocabulaire (sinon la casse forcée les impose partout)
_COMMON = {
    "LES", "DES", "UNE", "PAR", "SUR", "OUI", "NON", "PAS", "MAIS", "TOUT", "TOUS",
    "AVEC", "DANS", "POUR", "PLUS", "SANS", "SOUS", "VERS", "CES", "SES", "MES",
    "TES", "NOS", "VOS", "EST", "ONT", "FIN", "BON", "MAL", "BAS", "QUE", "QUI",
    "QUOI", "DONC", "ALORS", "AUSSI", "BIEN", "TRES", "TRÈS", "PEU", "ICI",
    "THE", "AND", "FOR", "YOU", "ARE", "NOT", "BUT", "ALL", "ANY", "CAN", "HAS",
}
_MAX_FILES = 3000
_MAX_BYTES = 200_000


def _candidates(text: str) -> list[str]:
    found = []
    for m in _ACRONYM.findall(text):
        if m not in _STOP and m not in _COMMON:
            found.append(m)
    for m in _MIXED.findall(text):
        if m not in _STOP and 3 <= len(m) <= 30:
            found.append(m)
    return found


def default_folders() -> list[str]:
    """Dossiers scannés par défaut si l'utilisateur n'en a pas choisi."""
    folders = []
    docs = Path.home() / "Documents"        # notes, comptes rendus, docs perso
    if docs.is_dir():
        folders.append(str(docs))
    return folders


def harvest(folders: list[str], min_count: int = 2) -> list[str]:
    counter: Counter = Counter()
    seen_files = 0
    for folder in folders:
        root = Path(folder)
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if seen_files >= _MAX_FILES:
                break
            if path.is_dir():
                if path.name in _SKIP_DIRS:
                    continue
                continue
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() not in _TEXT_EXT:
                continue
            try:
                if path.stat().st_size > _MAX_BYTES * 5:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")[:_MAX_BYTES]
            except (OSError, ValueError):
                continue
            seen_files += 1
            for term in _candidates(text):
                counter[term] += 1
    # garde les termes assez fréquents (acronymes/identifiants rares = bruit)
    return [t for t, c in counter.most_common() if c >= min_count]


# --------------------------------------------------------------------------
# cache (récolte + appris)
# --------------------------------------------------------------------------
def _load_cache() -> dict:
    import json
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    return {"harvested": [], "learned": [], "harvested_at": 0}


def _save_cache(data: dict) -> None:
    import json
    try:
        CACHE.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    except OSError:
        pass


def _dedupe(terms: list[str]) -> list[str]:
    """Déduplique sans tenir compte de la casse, garde la 1re orthographe vue
    (donc l'ordre de priorité : graine > appris > récolte)."""
    seen = {}
    for t in terms:
        k = t.lower()
        if k not in seen:
            seen[k] = t
    return list(seen.values())


def learn(text_or_terms, cfg: dict) -> None:
    """Mémorise les nouveaux termes vus dans une dictée corrigée."""
    if not cfg.get("vocab_learn", True):
        return
    if isinstance(text_or_terms, str):
        terms = _candidates(text_or_terms)
    else:
        terms = list(text_or_terms)
    if not terms:
        return
    cache = _load_cache()
    existing = {t.lower() for t in cache.get("learned", [])}
    added = False
    for t in terms:
        if t.lower() not in existing:
            cache.setdefault("learned", []).append(t)
            existing.add(t.lower())
            added = True
    if added:
        _save_cache(cache)


def build(cfg: dict, refresh: bool = False, max_age_h: float = 24.0) -> list[str]:
    """Vocabulaire final = graine + appris + récolte (dédupliqué, plafonné)."""
    seed = list(cfg.get("vocabulary", []))
    if not cfg.get("vocab_auto", True):
        return _dedupe(seed)[: cfg.get("vocab_max_terms", 400)]

    cache = _load_cache()
    learned = cache.get("learned", [])

    harvested = []
    if cfg.get("vocab_harvest", False):  # récolte fichiers : opt-in
        age_h = (time.time() - cache.get("harvested_at", 0)) / 3600
        if refresh or age_h > max_age_h or not cache.get("harvested"):
            folders = cfg.get("vocab_folders") or default_folders()
            cache["harvested"] = harvest(folders, cfg.get("vocab_min_count", 3))
            cache["harvested_at"] = time.time()
            _save_cache(cache)
        harvested = cache.get("harvested", [])

    # priorité d'orthographe : graine > appris > récolte
    merged = _dedupe(seed + learned + harvested)
    return merged[: cfg.get("vocab_max_terms", 400)]
