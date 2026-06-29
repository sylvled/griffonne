# Murmure 🎙️

Dictée vocale locale, rapide et **gratuite** — un équivalent de SuperWhisper.
Appuie sur un raccourci, parle, et le texte est **corrigé puis collé** dans
l'application active (Teams, Outlook, VS Code, Claude Code…).

- 🧠 **Transcription** : faster-whisper (`large-v3-turbo`) sur GPU (CUDA), repli CPU.
- ✨ **Correction automatique** par LLM local (Ollama) : noms propres, ponctuation,
  accents, hésitations — **sans aucun dictionnaire à remplir à la main**.
- 🌱 **Vocabulaire qui se construit tout seul** : il apprend tes termes au fil des dictées.
- 🖥️ **UI de réglages** + icône dans la barre des tâches.
- 🌐 **Mode distant** : dicte depuis un PC sans GPU, la transcription se fait sur ton PC GPU.
- 💸 **100 % local et gratuit** : aucune API, aucune donnée n'quitte tes machines.

---

## Démarrage rapide

| Je veux… | Je lance |
|---|---|
| **Dicter avec logs visibles** (le plus simple) | `run.bat` |
| **L'app complète** (icône barre des tâches + réglages) | `run_tray.bat` |
| **Démarrage auto** au login (sans fenêtre) | `install_autostart.bat` |
| **Serveur GPU** (pour le mode distant) | `serve.bat` |

Au 1er lancement, le modèle se charge (quelques secondes) puis l'app affiche **PRÊT**.

### Utilisation
1. Clique dans un champ texte (Bloc-notes, Teams, VS Code…).
2. **Ctrl+Alt+Espace** → parle (bip aigu).
3. **Ctrl+Alt+Espace** → fin (bip grave). Le texte corrigé se colle tout seul.
4. **Ctrl+Alt+Q** → quitter (mode console).

L'icône de la barre des tâches change de couleur : 🟡 chargement · 🟢 prêt ·
🔴 enregistrement · 🔵 transcription · ⚪ désactivée.

---

## Réglages (icône → « Réglages… »)

Tout est modifiable **sans éditer de fichier** :
- **Général** : modèle, GPU/CPU, langue, **micro**, raccourcis, auto-collage, volume des bips.
- **Correction** : nettoyage des hésitations, correction LLM (modèle, mode conservateur/light).
- **Vocabulaire** : apprentissage auto, récolte de fichiers (optionnelle), aperçu du vocabulaire.
- **Distant** : URL/jeton du serveur (client) ou host/port (serveur).

La config est stockée dans `config.json` (généré automatiquement). Sans ce
fichier, les valeurs par défaut de `murmure/config.py` s'appliquent.

---

## La correction automatique, en détail

Chaîne de traitement :

```
Whisper (audio→texte, amorcé par ton vocabulaire)
   → nettoyage (hésitations, bégaiements, corrections déterministes)
   → LLM local Ollama (corrige noms propres / ponctuation, SANS reformuler)
   → orthographe exacte de ton vocabulaire forcée
   → collé dans l'app active
```

**Le vocabulaire se construit tout seul** : à chaque dictée, les termes
techniques / noms propres que tu emploies sont mémorisés (fichier
`vocabulary.json`, géré par le programme). Plus tu l'utilises, plus il connaît
ton jargon. Tu peux aussi activer la récolte dans des fichiers de notes
(onglet Vocabulaire).

> Prérequis correction : [Ollama](https://ollama.com) installé + le modèle :
> `ollama pull qwen2.5:3b`. Si Ollama est absent, la dictée fonctionne quand
> même (sans la passe LLM).

---

## Mode distant (PC pro sans GPU → PC perso RTX 3080)

1. **Sur le PC GPU** (perso) : définis un jeton et lance le serveur.
   - Réglages → Distant → *Jeton* = un mot de passe ; *host* = `0.0.0.0`.
   - `serve.bat`
2. **Connecte tes deux PC** avec [Tailscale](https://tailscale.com) (gratuit,
   chiffré, sans ouvrir de port). Note l'IP Tailscale du PC GPU (`100.x.y.z`).
3. **Sur le PC pro** (client) :
   - Réglages → Général → *Mode* = `remote`.
   - Réglages → Distant → *URL du serveur* = `http://100.x.y.z:8765`, même *jeton*.
   - `run_tray.bat`

Tu dictes sur le PC pro, l'audio part chiffré vers le PC GPU, le texte revient
et se colle. ⚠️ **Toujours définir un jeton** si le serveur est accessible
au-delà de localhost.

---

## Dépannage

- **Rien ne se passe au raccourci** : lance le terminal **en administrateur**
  (capture clavier globale).
- **Transcription vide** : mauvais micro sélectionné (Réglages → Général → Micro).
- **Pas de correction** : Ollama n'est pas lancé, ou modèle absent
  (`ollama pull qwen2.5:3b`).
- **Lent** : c'est la passe LLM (~2-3 s). Tu peux la désactiver, choisir un
  modèle plus petit, ou passer le device en CPU si pas de GPU.

---

## Architecture (pour plus tard)

| Fichier | Rôle |
|---|---|
| `murmure/app.py` | Contrôleur : hotkey, capture, orchestration |
| `murmure/engine.py` | Transcription faster-whisper |
| `murmure/llm.py` | Correction par LLM local (Ollama) |
| `murmure/clean.py` | Nettoyage déterministe (hésitations, remplacements) |
| `murmure/vocab_builder.py` | Vocabulaire auto (apprentissage + récolte) |
| `murmure/backend.py` | Abstraction local / distant |
| `murmure/server.py` | Serveur de transcription distant |
| `murmure/tray.py` / `settings_ui.py` | Interface (tray + réglages) |
| `murmure/devices.py` / `audio.py` | GPU/micro, capture |

Modes de lancement : `python -m murmure` (app tray), `python -m murmure.app`
(console), `python -m murmure.server` (serveur).
