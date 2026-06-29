"""Application avec icône dans la barre des tâches (pystray) + fenêtre de
réglages (tkinter). C'est le mode « application » complet.

Lancement : python -m murmure   (ou Murmure.vbs / run_tray.bat)
Repli : si l'UI échoue, on bascule en mode console.
"""
import threading
import tkinter as tk

from . import config
from .app import BUSY, DISABLED, IDLE, LOADING, RECORDING, Murmure

_COLORS = {
    LOADING:   (190, 170, 60),
    IDLE:      (60, 160, 90),
    RECORDING: (210, 70, 70),
    BUSY:      (70, 120, 200),
    DISABLED:  (120, 120, 120),
}
_LABELS = {
    LOADING: "chargement…", IDLE: "prêt", RECORDING: "enregistrement",
    BUSY: "transcription…", DISABLED: "désactivée",
}


def _make_image(color):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=color)
    d.ellipse((24, 22, 40, 38), fill=(255, 255, 255, 230))  # pastille micro
    d.rectangle((30, 34, 34, 48), fill=(255, 255, 255, 230))
    return img


class TrayApp:
    def __init__(self):
        self.cfg = config.load()
        self.root = tk.Tk()
        self.root.withdraw()  # fenêtre racine cachée
        self.icon = None
        self.controller = Murmure(self.cfg, on_status=self._on_status)

    # ----------------------------------------------------------- statut/icone
    def _on_status(self, state):
        if self.icon is None:
            return
        try:
            self.icon.icon = _make_image(_COLORS.get(state, (120, 120, 120)))
            self.icon.title = f"Murmure — {_LABELS.get(state, state)}"
        except Exception:
            pass

    # -------------------------------------------------------------- actions
    def _toggle_enabled(self, icon, item):
        enabled = not self.cfg.get("enabled", True)
        self.cfg["enabled"] = enabled
        self.controller.set_enabled(enabled)
        merged = config.load()
        merged["enabled"] = enabled
        config.save(merged)

    def _open_settings(self, icon=None, item=None):
        # doit s'exécuter dans le thread tkinter principal
        self.root.after(0, self._open_settings_main)

    def _open_settings_main(self):
        from .settings_ui import SettingsWindow
        SettingsWindow(self.root, self.cfg, on_save=self._apply_settings)

    def _apply_settings(self, new_cfg):
        self.cfg = new_cfg
        self.controller.reload(new_cfg)

    def _quit(self, icon=None, item=None):
        try:
            self.controller.shutdown()
        finally:
            if self.icon is not None:
                self.icon.stop()
            self.root.after(0, self.root.quit)

    # ----------------------------------------------------------------- run
    def run(self):
        import pystray

        menu = pystray.Menu(
            pystray.MenuItem(
                "Dictée activée",
                self._toggle_enabled,
                checked=lambda item: self.cfg.get("enabled", True),
            ),
            pystray.MenuItem("Réglages…", self._open_settings),
            pystray.MenuItem("Quitter", self._quit),
        )
        self.icon = pystray.Icon(
            "murmure", _make_image(_COLORS[LOADING]), "Murmure — démarrage", menu)

        self.controller.start()
        self.icon.run_detached()
        self.root.mainloop()


def main():
    try:
        TrayApp().run()
    except Exception as exc:  # noqa: BLE001 — repli console si l'UI échoue
        print(f"[tray] UI indisponible ({exc!r}) — bascule en mode console.")
        Murmure().run_console()


if __name__ == "__main__":
    main()
