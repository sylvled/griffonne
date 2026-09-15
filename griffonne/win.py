"""Helpers Windows (ctypes) pour cibler la bonne fenêtre lors du collage.

On capture la fenêtre active au moment où l'utilisateur arrête l'écoute, puis
on lui redonne le focus juste avant de coller — ainsi le texte va toujours là
où l'utilisateur visait, même si le focus a bougé pendant la transcription."""
import sys

_WIN = sys.platform == "win32"
if _WIN:
    import ctypes
    _user32 = ctypes.windll.user32

_ALT = 0x12
_KEYUP = 0x0002
_SW_RESTORE = 9


def get_foreground_window():
    """Handle (hwnd) de la fenêtre active, ou None hors Windows."""
    if not _WIN:
        return None
    try:
        hwnd = _user32.GetForegroundWindow()
        return hwnd or None
    except Exception:  # noqa: BLE001
        return None


def focus_window(hwnd) -> bool:
    """Redonne le focus à la fenêtre `hwnd`. Renvoie True si probablement OK."""
    if not _WIN or not hwnd:
        return False
    try:
        if _user32.IsIconic(hwnd):            # restaurer si minimisée
            _user32.ShowWindow(hwnd, _SW_RESTORE)
        # Astuce connue : simuler une frappe ALT débloque le droit de Windows
        # à changer la fenêtre de premier plan depuis un autre processus.
        _user32.keybd_event(_ALT, 0, 0, 0)
        _user32.keybd_event(_ALT, 0, _KEYUP, 0)
        return bool(_user32.SetForegroundWindow(hwnd))
    except Exception:  # noqa: BLE001
        return False
