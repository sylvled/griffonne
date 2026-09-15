"""Fenêtre de réglages (tkinter). Édite la config sans toucher au JSON.
Au clic « Enregistrer & appliquer », sauvegarde puis appelle on_save(cfg)."""
import tkinter as tk
from tkinter import ttk

from . import config, vocab_builder
from .devices import list_microphones

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
        labels = ["Défaut système"] + [f"{m['index']}: {m['name']}" for m in mics]
        self._mic_map = {f"{m['index']}: {m['name']}": m["index"] for m in mics}
        cur = self.cfg.get("mic_device")
        sel = "Défaut système"
        for lab, idx in self._mic_map.items():
            if cur == idx:
                sel = lab
        v = tk.StringVar(value=sel)
        ttk.Combobox(f, textvariable=v, values=labels,
                     state="readonly").pack(side="left", fill="x", expand=True)
        self.vars["mic_device"] = v

        self._entry(t, "Raccourci (toggle)", "hotkey")
        self._entry(t, "Raccourci quitter", "quit_hotkey")
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
        merged = config.load()
        merged.update(self.cfg)
        config.save(merged)
        if self.on_save:
            self.on_save(merged)
        self.win.destroy()


def open_settings(cfg: dict, on_save):
    """Ouvre la fenêtre en autonome (mode console)."""
    SettingsWindow(None, cfg, on_save)
    tk.mainloop()
