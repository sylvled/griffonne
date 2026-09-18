"""Raccourcis clavier : normalisation tolérante (français / anglais, casse,
espaces), validation AVANT application, affichage lisible.

Forme canonique stockée en config : 'ctrl+alt+m', 'ctrl+space', 'f9'...
"""
import re

MODIFIERS = {"ctrl", "ctrl_l", "ctrl_r", "alt", "alt_l", "alt_r", "alt_gr",
             "shift", "shift_r", "cmd", "cmd_r"}

_ALIASES = {
    # modificateurs
    "ctrl": "ctrl", "control": "ctrl", "ctl": "ctrl", "contrôle": "ctrl",
    "controle": "ctrl", "ctrl gauche": "ctrl_l", "ctrl droit": "ctrl_r",
    "alt": "alt", "altgr": "alt_gr", "alt gr": "alt_gr", "alt_gr": "alt_gr",
    "shift": "shift", "maj": "shift", "majuscule": "shift",
    "win": "cmd", "windows": "cmd", "super": "cmd", "cmd": "cmd", "meta": "cmd",
    # touches spéciales
    "space": "space", "espace": "space", "spc": "space", "barre espace": "space",
    "enter": "enter", "entrée": "enter", "entree": "enter", "return": "enter",
    "retour": "enter",
    "esc": "esc", "escape": "esc", "échap": "esc", "echap": "esc",
    "tab": "tab", "tabulation": "tab",
    "backspace": "backspace", "retour arrière": "backspace",
    "delete": "delete", "del": "delete", "suppr": "delete",
    "insert": "insert", "inser": "insert", "ins": "insert",
    "home": "home", "début": "home", "debut": "home", "origine": "home",
    "end": "end", "fin": "end",
    "pageup": "page_up", "page_up": "page_up", "pgup": "page_up",
    "page précédente": "page_up", "page precedente": "page_up",
    "pagedown": "page_down", "page_down": "page_down", "pgdn": "page_down",
    "page suivante": "page_down",
    "up": "up", "haut": "up", "down": "down", "bas": "down",
    "left": "left", "gauche": "left", "right": "right", "droite": "right",
    "pause": "pause",
    "scrolllock": "scroll_lock", "scroll_lock": "scroll_lock",
    "arrêt défil": "scroll_lock", "arret defil": "scroll_lock",
    "printscreen": "print_screen", "print_screen": "print_screen",
    "impr écran": "print_screen", "impr ecran": "print_screen", "impr": "print_screen",
    "menu": "menu", "capslock": "caps_lock", "caps_lock": "caps_lock",
    "verr maj": "caps_lock", "numlock": "num_lock", "num_lock": "num_lock",
    "verr num": "num_lock",
}

_PRETTY = {
    "ctrl": "Ctrl", "ctrl_l": "Ctrl gauche", "ctrl_r": "Ctrl droit",
    "alt": "Alt", "alt_l": "Alt gauche", "alt_r": "Alt droit", "alt_gr": "AltGr",
    "shift": "Maj", "shift_r": "Maj droite", "cmd": "Win", "cmd_r": "Win droit",
    "space": "Espace", "enter": "Entrée", "esc": "Échap", "tab": "Tab",
    "backspace": "Retour arrière", "delete": "Suppr", "insert": "Inser",
    "home": "Début", "end": "Fin", "page_up": "Page ↑", "page_down": "Page ↓",
    "up": "↑", "down": "↓", "left": "←", "right": "→", "pause": "Pause",
    "scroll_lock": "Arrêt défil", "print_screen": "Impr écran", "menu": "Menu",
    "caps_lock": "Verr maj", "num_lock": "Verr num",
}

# codes de touche virtuelle Windows des touches non-modificatrices (pour
# attendre leur relâchement avant de coller)
_VK = {"space": 0x20, "enter": 0x0D, "tab": 0x09, "esc": 0x1B, "backspace": 0x08,
       "delete": 0x2E, "insert": 0x2D, "home": 0x24, "end": 0x23, "page_up": 0x21,
       "page_down": 0x22, "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
       "pause": 0x13, "scroll_lock": 0x91, "print_screen": 0x2C, "menu": 0x5D,
       "caps_lock": 0x14, "num_lock": 0x90}


def normalize(combo: str) -> str:
    """'Ctrl + Espace' -> 'ctrl+space'. Lève ValueError avec un message clair."""
    if not combo or not combo.strip():
        raise ValueError("raccourci vide")
    parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
    out = []
    for p in parts:
        if p in _ALIASES:
            out.append(_ALIASES[p])
        elif re.fullmatch(r"f([1-9]|1\d|2[0-4])", p):
            out.append(p)
        elif len(p) == 1:
            out.append(p)
        else:
            raise ValueError(f"touche inconnue : « {p} »")
    mods = [m for m in out if m in MODIFIERS]
    keys = [k for k in out if k not in MODIFIERS]
    if len(keys) != 1:
        raise ValueError("il faut exactement une touche principale "
                         "(lettre, chiffre, F1-F24, Espace...) avec ou sans "
                         "modificateurs")
    return "+".join(dict.fromkeys(mods)) + ("+" if mods else "") + keys[0]


def to_pynput(combo: str) -> str:
    """Forme pynput ('<ctrl>+<space>'), validée par pynput lui-même."""
    from pynput.keyboard import HotKey
    parts = normalize(combo).split("+")
    spec = "+".join(p if len(p) == 1 else f"<{p}>" for p in parts)
    HotKey.parse(spec)  # ValueError si pynput ne connaît pas une touche
    return spec


def validate(combo: str) -> tuple[bool, str]:
    """(True, forme canonique) ou (False, message d'erreur)."""
    try:
        to_pynput(combo)
        return True, normalize(combo)
    except ValueError as exc:
        return False, str(exc)


def pretty(combo: str) -> str:
    """'ctrl+alt+m' -> 'Ctrl + Alt + M'."""
    try:
        parts = normalize(combo).split("+")
    except ValueError:
        return combo
    return " + ".join(_PRETTY.get(p, p.upper()) for p in parts)


def vk_codes(combo: str) -> list[int]:
    """Codes VK des touches non-modificatrices (attente de relâchement)."""
    try:
        parts = normalize(combo).split("+")
    except ValueError:
        return []
    vks = []
    for p in parts:
        if p in MODIFIERS:
            continue
        if p in _VK:
            vks.append(_VK[p])
        elif re.fullmatch(r"f\d+", p):
            vks.append(0x70 + int(p[1:]) - 1)
        elif len(p) == 1 and p.isalnum():
            vks.append(ord(p.upper()))
    return vks
