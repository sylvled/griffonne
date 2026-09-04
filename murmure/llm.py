"""Passe de correction par LLM local (Ollama). Corrige le texte transcrit en
contexte : noms propres, homophones, ponctuation, et surtout le vocabulaire
propre à l'utilisateur (fourni en liste). Tout est local et gratuit.

Si Ollama est indisponible, on renvoie le texte d'origine (jamais de plantage)."""
import json
import urllib.request

_RULES_CONSERVATIVE = (
    "Tu corriges une transcription vocale française. Corrige uniquement la "
    "ponctuation, les majuscules, les accents et les mots clairement mal "
    "transcrits.\n"
    "RÈGLES ABSOLUES :\n"
    "- Ne reformule pas. Ne change ni l'ordre ni le choix des mots, conserve le "
    "style oral.\n"
    "- N'ajoute ni ne supprime aucun mot (sauf une hésitation évidente : euh, "
    "heu).\n"
    "- Noms propres / termes techniques : remplace un mot UNIQUEMENT s'il est "
    "une déformation phonétique ÉVIDENTE d'un terme du vocabulaire ci-dessous "
    "(ex. « esquissi » → « ESXi », « cloud code » → « Claude Code »). Ne "
    "remplace jamais un nom propre déjà correct par un autre. Dans le doute, "
    "ne change rien.\n"
    "- Ne traduis pas. Réponds UNIQUEMENT par le texte corrigé, sans guillemets "
    "ni commentaire ni préfixe."
)

_RULES_LIGHT = (
    "Tu es un correcteur de transcription vocale française. Corrige les erreurs "
    "de reconnaissance vocale (mots mal transcrits, homophones, noms propres et "
    "termes techniques), la ponctuation et les majuscules. Tu peux aussi nettoyer "
    "légèrement le style oral : retirer répétitions et hésitations, transformer "
    "les tournures orales en formulation écrite claire, SANS changer le sens ni "
    "le propos. Ne traduis pas. Réponds UNIQUEMENT par le texte corrigé, sans "
    "guillemets ni commentaire."
)

def _build_system(mode: str, vocabulary: list[str] | None) -> str:
    rules = _RULES_LIGHT if mode == "light" else _RULES_CONSERVATIVE
    vocab = ""
    if vocabulary:
        vocab = ("\n\nVOCABULAIRE (orthographe exacte) : "
                 + ", ".join(vocabulary) + ".")
    return rules + vocab


class Corrector:
    def __init__(self, model="qwen2.5:3b", mode="conservative",
                 url="http://127.0.0.1:11434", enabled=True, vocabulary=None,
                 keep_alive="30m"):
        self.model = model
        # « localhost » coûte ~2 s par appel sous Windows (tentative IPv6 ::1
        # avant repli IPv4). On normalise systématiquement.
        self.url = url.rstrip("/").replace("//localhost:", "//127.0.0.1:")
        self.keep_alive = keep_alive
        self.enabled = enabled
        self.mode = mode
        self.vocabulary = vocabulary or []
        self.system = _build_system(mode, self.vocabulary)

    def _call(self, text: str, timeout: float) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system},
                {"role": "user", "content": text},
            ],
            "stream": False,
            "options": {"temperature": 0},
            "keep_alive": self.keep_alive,  # évite le rechargement du modèle
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.url + "/api/chat", data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
        return resp["message"]["content"]

    def correct(self, text: str, timeout: float = 20.0) -> str:
        if not self.enabled or not text:
            return text
        try:
            out = self._call(text, timeout)
        except Exception as exc:  # noqa: BLE001
            print(f"[llm] correction ignorée ({exc!r})")
            return text
        out = out.strip().strip('"').strip()
        if out:
            from .clean import enforce_vocab
            out = enforce_vocab(out, self.vocabulary)
        return out or text

    def warmup(self) -> None:
        """Charge le modèle en VRAM pour éviter le coût à froid au 1er usage."""
        if self.enabled:
            try:
                self._call("ok", timeout=120)
            except Exception:  # noqa: BLE001
                pass
