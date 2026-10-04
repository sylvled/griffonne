"""Modes de dictée : un mot déclencheur en début de dictée change le
traitement appliqué au texte.

Par défaut, Griffonne transcrit fidèlement. En disant « Mail, ... », le texte
dicté — même brut et désordonné — est RÉÉCRIT en message structuré par un LLM.

Les modes sont décrits dans la configuration (clé `modes`), ce qui permet d'en
ajouter d'autres sans toucher au code."""
import re
import unicodedata


def _fold(s: str) -> str:
    """Minuscules sans accents ni ponctuation, pour comparer les déclencheurs."""
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def detect(text: str, cfg: dict) -> tuple[str | None, str]:
    """Renvoie (nom_du_mode, texte_sans_le_déclencheur).

    Le déclencheur doit être le tout premier mot de la dictée ; il est retiré
    du texte transmis au modèle. Si aucun mode ne correspond : (None, texte)."""
    if not text or not cfg.get("modes_enabled", True):
        return None, text
    modes = cfg.get("modes") or {}
    head = _fold(text).split()
    if not head:
        return None, text
    for name, spec in modes.items():
        for trig in spec.get("triggers", []):
            words = _fold(trig).split()
            if words and head[: len(words)] == words:
                # retire le déclencheur du texte d'origine (accents, casse et
                # ponctuation éventuelle : « Mail, » / « E-mail : »)
                pattern = r"^\W*" + r"\W+".join(
                    r"\w+" for _ in words) + r"\s*[,.:;!?-]*\s*"
                body = re.sub(pattern, "", text, count=1).lstrip()
                return name, (body or text)
    return None, text


def describe(cfg: dict) -> str:
    """Résumé lisible des modes actifs (pour le log au démarrage)."""
    modes = cfg.get("modes") or {}
    if not cfg.get("modes_enabled", True) or not modes:
        return "aucun"
    return ", ".join(f"{n} ({'/'.join(s.get('triggers', [])[:3])})"
                     for n, s in modes.items())
