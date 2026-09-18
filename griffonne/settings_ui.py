"""Fenêtre de réglages (tkinter). Édite la config sans toucher au JSON.
Au clic « Enregistrer & appliquer », sauvegarde puis appelle on_save(cfg)."""
import tkinter as tk
from tkinter import messagebox, ttk

from . import config, hotkeys, vocab_builder
from .devices import list_microphones, mic_label

ENGINES = ["whisper", "parakeet"]
MODELS = ["large-v3-turbo", "large-v3", "medium", "small", "base"]
DEVICES = ["auto", "cuda", "cpu"]
LLM_MODES = ["conservative", "light"]
BACKENDS = ["local", "remote", "auto"]


class SettingsWindow:
    def __init__(self, master, cfg: dict, on_save):
        self.cfg = dict(cfg)
        self.on_save = on_save
        self.win = tk.Toplevel(master) if master else tk.Tk()
        self.win.title("Griffonne — Réglages")
        self.win.geometry("560x560")
        self.vars: dict = {}

        nb = ttk.Notebook(self.win)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        self._tab_general(nb)
        self._tab_correction(nb)
        self._tab_vocab(nb)
        self._tab_remote(nb)

        bar = ttk.Frame(self.win)
        bar.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(bar, text="Enregistrer & appliquer",
                   command=self._save).pack(side="right")
        ttk.Button(bar, text="Fermer",
                   command=self.win.destroy).pack(side="right", padx=6)

    # ---------------------------------------------------------------- helpers
    def _row(self, parent, label):
        f = ttk.Frame(parent)
        f.pack(fill="x", pady=4)
        ttk.Label(f, text=label, width=22).pack(side="left")
        return f

    def _combo(self, parent, label, key, values):
        f = self._row(parent, label)
        v = tk.StringVar(value=str(self.cfg.get(key, "")))
        ttk.Combobox(f, textvariable=v, values=values,
                     state="readonly").pack(side="left", fill="x", expand=True)
        self.vars[key] = v

    def _entry(self, parent, label, key):
        f = self._row(parent, label)
        v = tk.StringVar(value=str(self.cfg.get(key, "") or ""))
        ttk.Entry(f, textvariable=v).pack(side="left", fill="x", expand=True)
        self.vars[key] = v

    def _check(self, parent, label, key):
        v = tk.BooleanVar(value=bool(self.cfg.get(key, False)))
        ttk.Checkbutton(parent, text=label, variable=v).pack(anchor="w", pady=3)
        self.vars[key] = v

    def _scale(self, parent, label, key, lo, hi):
        f = self._row(parent, label)
        v = tk.DoubleVar(value=float(self.cfg.get(key, lo)))
        ttk.Scale(f, from_=lo, to=hi, variable=v).pack(
            side="left", fill="x", expand=True)
        self.vars[key] = v

    def _hotkey_row(self, parent, label, key):
        f = self._row(parent, label)
        v = tk.StringVar(value=str(self.cfg.get(key, "") or ""))
        ttk.Entry(f, textvariable=v, width=22).pack(side="left")
        ttk.Button(f, text="Capturer…",
                   command=lambda: self._capture_hotkey(v)).pack(side="left", padx=4)
        status = ttk.Label(f, text="", width=26)
        status.pack(side="left")
        self.vars[key] = v

        def refresh(*_):
            combo = v.get().strip()
            if not combo:
                status.config(text="(désactivé)" if key == "quit_hotkey" else "requis",
                              foreground="gray" if key == "quit_hotkey" else "red")
                return
            ok, msg = hotkeys.validate(combo)
            status.config(text=("✓ " + hotkeys.pretty(msg)) if ok else ("✗ " + msg),
                          foreground="green" if ok else "red")
        v.trace_add("write", refresh)
        refresh()

    def _capture_hotkey(self, var):
        """Petite fenêtre modale : appuie sur la combinaison, elle est lue."""
        dlg = tk.Toplevel(self.win)
        dlg.title("Capture du raccourci")
        dlg.geometry("420x150")
        dlg.transient(self.win)
        dlg.grab_set()
        ttk.Label(dlg, text="Appuie sur la combinaison voulue\n"
                  "(Échap seul = annuler)", justify="center").pack(pady=(12, 4))
        preview = ttk.Label(dlg, text="…", font=("", 14, "bold"))
        preview.pack(pady=4)
        held: set[str] = set()
        _MOD = {"Control_L": "ctrl", "Control_R": "ctrl", "Alt_L": "alt", "Alt_R": "alt",
                "Shift_L": "shift", "Shift_R": "shift", "Win_L": "cmd", "Win_R": "cmd",
                "Super_L": "cmd", "Super_R": "cmd", "Meta_L": "cmd", "Meta_R": "cmd"}
        _KEY = {"space": "space", "Return": "enter", "KP_Enter": "enter", "Escape": "esc",
                "Tab": "tab", "BackSpace": "backspace", "Delete": "delete",
                "Insert": "insert", "Home": "home", "End": "end", "Prior": "page_up",
                "Next": "page_down", "Up": "up", "Down": "down", "Left": "left",
                "Right": "right", "Pause": "pause", "Scroll_Lock": "scroll_lock",
                "Print": "print_screen", "Snapshot": "print_screen", "App": "menu",
                "Menu": "menu", "Caps_Lock": "caps_lock", "Num_Lock": "num_lock"}

        def show():
            order = [m for m in ("ctrl", "alt", "shift", "cmd") if m in held]
            preview.config(text=hotkeys.pretty("+".join(order)) if order else "…")

        def on_press(e):
            ks = e.keysym
            if ks in _MOD:
                held.add(_MOD[ks]); show(); return "break"
            if ks == "Escape" and not held:
                dlg.destroy(); return "break"
            if ks in _KEY:
                key = _KEY[ks]
            elif ks.startswith("F") and ks[1:].isdigit():
                key = ks.lower()
            elif len(ks) == 1 or (len(e.char) == 1 and e.char.isprintable()):
                key = (ks if len(ks) == 1 else e.char).lower()
            else:
                return "break"  # touche non gérée : on ignore
            order = [m for m in ("ctrl", "alt", "shift", "cmd") if m in held]
            combo = "+".join(order + [key])
            ok, msg = hotkeys.validate(combo)
            if ok:
                var.set(msg); dlg.destroy()
            else:
                preview.config(text="✗ " + msg)
            return "break"

        def on_release(e):
            m = _MOD.get(e.keysym)
            if m:
                held.discard(m); show()
            return "break"

        dlg.bind("<KeyPress>", on_press)
        dlg.bind("<KeyRelease>", on_release)
        ttk.Button(dlg, text="Annuler", command=dlg.destroy).pack(pady=6)
        dlg.focus_force()

    # ------------------------------------------------------------------- tabs
    def _tab_general(self, nb):
        t = ttk.Frame(nb)
        nb.add(t, text="Général")
        self._combo(t, "Mode (backend)", "backend", BACKENDS)
        self._combo(t, "Moteur", "engine", ENGINES)
        ttk.Label(t, text="whisper = précision max (amorce vocabulaire, langue forcée)\n"
                  "parakeet = très rapide même sur CPU (langue auto-détectée)",
                  foreground="gray").pack(anchor="w", padx=4)
        self._combo(t, "Modèle (Whisper)", "model", MODELS)
        self._combo(t, "Calcul (device)", "device", DEVICES)
        self._entry(t, "Langue (fr, en, ...)", "language")

        # micro
        f = self._row(t, "Micro")
        mics = list_microphones()
        labels = ["Défaut système"] + [mic_label(m) for m in mics]
        self._mic_map = {mic_label(m): m["spec"] for m in mics}   # libellé -> "nom|API"
        cur = self.cfg.get("mic_device")
        sel = "Défaut système"
        for m in mics:   # retrouve la sélection : identifiant stable ou ancien index
            if cur == m["spec"] or cur == m["index"]:
                sel = mic_label(m)
        v = tk.StringVar(value=sel)
        ttk.Combobox(f, textvariable=v, values=labels,
                     state="readonly").pack(side="left", fill="x", expand=True)
        self.vars["mic_device"] = v

        self._hotkey_row(t, "Raccourci dictée", "hotkey")
        self._hotkey_row(t, "Raccourci quitter (vide = aucun)", "quit_hotkey")
        ttk.Label(t, text="Clique « Capturer… » puis appuie sur la combinaison voulue. "
                  "Tu peux aussi taper « ctrl+alt+m », « Ctrl + Espace », « F9 »…",
                  foreground="gray", wraplength=520).pack(anchor="w", pady=(0, 4))
        self._check(t, "Coller automatiquement le texte", "auto_paste")
        self._check(t, "Bip sonore début/fin", "beep")
        self._scale(t, "Volume des bips", "beep_volume", 0.0, 0.5)

    def _tab_correction(self, nb):
        t = ttk.Frame(nb)
        nb.add(t, text="Correction")
        self._check(t, "Nettoyer hésitations (euh, heu...)", "clean_fillers")
        self._check(t, "Correction par LLM local (Ollama)", "llm_correct")
        self._entry(t, "Modèle LLM (Ollama)", "llm_model")
        self._combo(t, "Mode LLM", "llm_mode", LLM_MODES)
        self._entry(t, "URL Ollama", "ollama_url")
        ttk.Label(t, text="Mode conservateur = corrige sans reformuler.\n"
                  "Mode light = nettoie aussi le style oral.",
                  foreground="gray").pack(anchor="w", pady=6)

    def _tab_vocab(self, nb):
        t = ttk.Frame(nb)
        nb.add(t, text="Vocabulaire")
        self._check(t, "Vocabulaire automatique", "vocab_auto")
        self._check(t, "Apprendre les termes au fil des dictées", "vocab_learn")
        self._check(t, "Récolter aussi dans des fichiers (prose)", "vocab_harvest")
        f = self._row(t, "Dossiers (1 par ligne)")
        f.pack_forget()
        ttk.Label(t, text="Dossiers à scanner (un par ligne, vide = auto) :").pack(
            anchor="w")
        self._folders_txt = tk.Text(t, height=3)
        self._folders_txt.pack(fill="x")
        self._folders_txt.insert("1.0", "\n".join(self.cfg.get("vocab_folders", [])))

        ttk.Button(t, text="Rafraîchir la récolte maintenant",
                   command=self._refresh_vocab).pack(anchor="w", pady=6)
        ttk.Label(t, text="Vocabulaire actuel :").pack(anchor="w")
        self._vocab_view = tk.Text(t, height=8)
        self._vocab_view.pack(fill="both", expand=True)
        self._fill_vocab_view()

    def _tab_remote(self, nb):
        t = ttk.Frame(nb)
        nb.add(t, text="Distant")
        ttk.Label(t, text="CLIENT (ce PC se connecte à un serveur GPU) :",
                  font=("", 9, "bold")).pack(anchor="w", pady=(2, 0))
        self._entry(t, "URL du serveur", "remote_url")
        self._entry(t, "Jeton (token)", "remote_token")
        ttk.Separator(t).pack(fill="x", pady=8)
        ttk.Label(t, text="SERVEUR (ce PC fait la transcription) :",
                  font=("", 9, "bold")).pack(anchor="w")
        self._entry(t, "Écoute (host)", "server_host")
        self._entry(t, "Port", "server_port")
        ttk.Label(t, text="Astuce : relie tes PC avec Tailscale (gratuit,\n"
                  "chiffré) et mets l'IP Tailscale + un jeton.",
                  foreground="gray").pack(anchor="w", pady=6)

    # --------------------------------------------------------------- actions
    def _fill_vocab_view(self):
        try:
            terms = vocab_builder.build(self.cfg)
        except Exception:
            terms = self.cfg.get("vocabulary", [])
        self._vocab_view.delete("1.0", "end")
        self._vocab_view.insert("1.0", ", ".join(terms))

    def _refresh_vocab(self):
        self._collect()
        try:
            vocab_builder.build(self.cfg, refresh=True)
        except Exception:
            pass
        self._fill_vocab_view()

    def _collect(self):
        for key, var in self.vars.items():
            self.cfg[key] = var.get()
        # micro -> index ou None
        micsel = self.vars["mic_device"].get()
        self.cfg["mic_device"] = self._mic_map.get(micsel)  # None si "Défaut"
        # types
        self.cfg["server_port"] = int(float(self.cfg.get("server_port", 8765)))
        self.cfg["beep_volume"] = round(float(self.cfg.get("beep_volume", 0.05)), 3)
        if not self.cfg.get("language"):
            self.cfg["language"] = None
        # dossiers
        folders = [l.strip() for l in
                   self._folders_txt.get("1.0", "end").splitlines() if l.strip()]
        self.cfg["vocab_folders"] = folders

    def _save(self):
        self._collect()
        # raccourcis : validés et normalisés AVANT toute sauvegarde
        for key, label in (("hotkey", "Raccourci dictée"), ("quit_hotkey", "Raccourci quitter")):
            combo = (self.cfg.get(key) or "").strip()
            if not combo:
                if key == "hotkey":
                    messagebox.showerror("Raccourci", "Le raccourci de dictée est requis.",
                                         parent=self.win)
                    return
                self.cfg[key] = ""
                continue
            ok, msg = hotkeys.validate(combo)
            if not ok:
                messagebox.showerror("Raccourci invalide", f"{label} : {msg}", parent=self.win)
                return
            self.cfg[key] = msg  # forme canonique (ex. ctrl+space)
        merged = config.load()
        merged.update(self.cfg)
        try:
            if self.on_save:
                self.on_save(merged)   # recharge le contrôleur (peut refuser)
        except ValueError as exc:
            messagebox.showerror("Réglages non appliqués", str(exc), parent=self.win)
            return
        config.save(merged)          # sauvegardé seulement si appliqué
        self.win.destroy()


def open_settings(cfg: dict, on_save):
    """Ouvre la fenêtre en autonome (mode console)."""
    SettingsWindow(None, cfg, on_save)
    tk.mainloop()
