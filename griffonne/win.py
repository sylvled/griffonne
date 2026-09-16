"""Helpers Windows (ctypes) pour coller au bon endroit.

À l'arrêt de l'écoute on mémorise la fenêtre active ET le contrôle qui a le
focus dedans. Avant de coller : on attend que les touches du raccourci soient
physiquement relâchées (sinon Ctrl+V devient Ctrl+Alt+V), on remet la fenêtre
au premier plan sans simuler de touche ALT (un ALT seul déplace le focus vers
la barre de menus), puis on redonne le focus au contrôle mémorisé."""
import sys
import time

_WIN = sys.platform == "win32"
if _WIN:
    import ctypes
    from ctypes import wintypes
    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32
    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]

VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN = 0x10, 0x11, 0x12, 0x5B, 0x5C
_MODIFIERS = (VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN)
_SW_RESTORE = 9


def _thread_of(hwnd) -> int:
    pid = wintypes.DWORD()
    return _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))


if _WIN:
    class _MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                    ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class _INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("mi", _MOUSEINPUT)]


def _nudge_mouse() -> None:
    """Mouvement souris de (0, 0) : invisible, mais compte comme une entrée."""
    inp = _INPUT(0, _MOUSEINPUT(0, 0, 0, 0x0001, 0, None))  # MOUSEEVENTF_MOVE
    _user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def get_foreground_window():
    if not _WIN:
        return None
    try:
        return _user32.GetForegroundWindow() or None
    except Exception:  # noqa: BLE001
        return None


def window_title(hwnd) -> str:
    if not _WIN or not hwnd:
        return ""
    buf = ctypes.create_unicode_buffer(256)
    _user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value


def get_focused_control(hwnd):
    """Handle du contrôle qui a le focus clavier dans la fenêtre `hwnd`."""
    if not _WIN or not hwnd:
        return None
    cur, tid = _kernel32.GetCurrentThreadId(), _thread_of(hwnd)
    if not tid or tid == cur:
        return None
    if not _user32.AttachThreadInput(cur, tid, True):
        return None
    try:
        return _user32.GetFocus() or None
    finally:
        _user32.AttachThreadInput(cur, tid, False)


def wait_keys_released(extra_vks=(), timeout: float = 2.0) -> bool:
    """Attend que modificateurs (et touches données) soient relâchés."""
    if not _WIN:
        return True
    vks = tuple(_MODIFIERS) + tuple(extra_vks)
    end = time.time() + timeout
    while time.time() < end:
        if all(not (_user32.GetAsyncKeyState(vk) & 0x8000) for vk in vks):
            return True
        time.sleep(0.02)
    return False


def focus_window(hwnd, control=None) -> bool:
    """Remet `hwnd` au premier plan (si nécessaire) puis le focus sur `control`."""
    if not _WIN or not hwnd or not _user32.IsWindow(hwnd):
        return False
    try:
        if _user32.IsIconic(hwnd):
            _user32.ShowWindow(hwnd, _SW_RESTORE)
        ok = True
        if _user32.GetForegroundWindow() != hwnd:
            # SetForegroundWindow est refusé aux processus « non actifs ».
            # Méthode validée empiriquement (sans simuler de touche) : attacher
            # notre file d'entrée à celle du premier plan ET de la cible, puis
            # BringWindowToTop + SetForegroundWindow.
            cur = _kernel32.GetCurrentThreadId()
            fg = _user32.GetForegroundWindow()
            tids = {t for t in (_thread_of(fg) if fg else 0, _thread_of(hwnd))
                    if t and t != cur}
            attached = [t for t in tids if _user32.AttachThreadInput(cur, t, True)]
            try:
                _user32.BringWindowToTop(hwnd)
                _user32.SetForegroundWindow(hwnd)
            finally:
                for t in attached:
                    _user32.AttachThreadInput(cur, t, False)
            ok = _user32.GetForegroundWindow() == hwnd
            if not ok:
                # secours : un mouvement souris nul via SendInput fait de nous
                # le « dernier processus ayant produit une entrée », ce qui
                # autorise SetForegroundWindow. Aucun effet visible.
                _nudge_mouse()
                _user32.SetForegroundWindow(hwnd)
                ok = _user32.GetForegroundWindow() == hwnd
        if control and _user32.IsWindow(control):
            cur, tid = _kernel32.GetCurrentThreadId(), _thread_of(hwnd)
            if tid and tid != cur and _user32.AttachThreadInput(cur, tid, True):
                try:
                    _user32.SetFocus(control)
                finally:
                    _user32.AttachThreadInput(cur, tid, False)
        return ok
    except Exception:  # noqa: BLE001
        return False
