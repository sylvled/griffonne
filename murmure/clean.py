"""Nettoyage du texte transcrit : suppression des hésitations (euh, heu, hmm...),
des bégaiements de mots-outils (« je je »), et remise en forme légère."""
import re

# interjections d'hésitation, avec allongements (euuuh, heuuu, hmmm, mmmh...).
# Le « h » final est exigé pour la famille « euh » afin de NE PAS supprimer le
# mot français « eu » (j'ai eu...).
_FILLER_RE = re.compile(
    r"(?i)\b(?:h?e+u+h+|h+e+u+h*|hu+m+|h+m+h*|m+h+|mm+|bah)\b"
)

# bégaiements sur des mots-outils courts (« je je veux », « le le chat »).
# Volontairement limité pour ne PAS toucher les répétitions légitimes
# comme « très très bien ».
_STUTTER_RE = re.compile(
    r"(?i)\b(je|tu|il|elle|on|nous|vous|le|la|les|de|des|un|une|et|que|qui|à|au|"
    r"ce|cette|mon|ma|mes|son|sa|ses|dans|pour|avec|sur)(?:\s+\1\b)+"
)


def enforce_vocab(text: str, vocabulary: list[str] | None) -> str:
    """Force l'orthographe/casse exacte des termes du vocabulaire
    (« vera » -> « VERA », « claude code » -> « Claude Code »).
    Déterministe et instantané : fonctionne SANS LLM (utile en mode CPU)."""
    if not text or not vocabulary:
        return text
    for term in vocabulary:
        text = re.sub(rf"\b{re.escape(term)}\b", term, text, flags=re.IGNORECASE)
    return text


def _apply_replacements(s: str, replacements: dict | None) -> str:
    if not replacements:
        return s
    for wrong, right in replacements.items():
        s = re.sub(rf"\b{re.escape(wrong)}\b", right, s, flags=re.IGNORECASE)
    return s


def clean_text(text: str, remove_fillers: bool = True,
               replacements: dict | None = None) -> str:
    if not text:
        return text
    s = _apply_replacements(text, replacements)
    if remove_fillers:
        s = _FILLER_RE.sub("", s)
        s = _STUTTER_RE.sub(r"\1", s)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)   # espace avant ponctuation
    s = re.sub(r"\s{2,}", " ", s)            # espaces multiples
    s = re.sub(r"^[\s,;:.\-]+", "", s).strip()  # ponctuation parasite en tête
    if s:
        s = s[0].upper() + s[1:]
    return s
