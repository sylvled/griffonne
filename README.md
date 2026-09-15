# Griffonne 🎙️

Dictée vocale **locale, rapide et gratuite** pour Windows. Un raccourci, tu
parles, et le texte — transcrit, corrigé, mis en forme — est collé dans
l'application active (traitement de texte, messagerie, terminal, IDE…).

- 🧠 **Deux moteurs au choix** : Whisper `large-v3-turbo` (précision) ou NVIDIA
  Parakeet 0.6B (vitesse, fonctionne sans GPU). Bascule à tout moment.
- ✨ **Correction automatique** par LLM local (Ollama) : noms propres,
  ponctuation, accents — sans reformuler.
- 🌱 **Vocabulaire qui s'apprend tout seul** : les termes techniques et noms
  propres que tu dictes sont mémorisés et réutilisés.
- 🧹 **Nettoyage des hésitations** (« euh », « heu », bégaiements).
- 🖥️ Icône dans la barre des tâches + fenêtre de réglages.
- 🌐 **Mode distant** optionnel : un PC sans GPU délègue la transcription à un
  PC équipé, avec repli local automatique.
- 🔒 **100 % local** : aucune API cloud, aucune donnée ne quitte tes machines.

---

## Installation

Prérequis : Windows 10/11, [Python 3.11+](https://www.python.org/downloads/).
Pour la correction automatique : [Ollama](https://ollama.com) puis
`ollama pull qwen2.5:3b` (facultatif — sans Ollama, la dictée fonctionne sans
la passe LLM).

| Ta machine | Installation |
|---|---|
| **Avec GPU NVIDIA** | `python -m venv .venv` puis `.venv\Scripts\pip install -r requirements.txt` |
| **Sans GPU** | `install_cpu.bat` (moteur Parakeet, sans les 1,9 Go de bibliothèques CUDA) |

## Lancer

| Je veux… | Je lance |
|---|---|
| Dicter avec les logs visibles (le plus simple) | `run.bat` |
| L'app complète (icône barre des tâches + réglages) | `run_tray.bat` |
| Le démarrage automatique à l'ouverture de session | `install_autostart.bat` |
| Le serveur de transcription (mode distant) | `serve.bat` |

Au premier lancement le modèle se télécharge (~1,6 Go pour Whisper turbo,
~600 Mo pour Parakeet) puis l'app affiche **PRÊT**.

### Utilisation

1. Clique dans un champ texte.
2. **Ctrl+Alt+M** → parle (bip aigu).
3. **Ctrl+Alt+M** → fin (bip grave). Le texte corrigé se colle tout seul.
4. Pour quitter : menu de l'icône → **Quitter**.

Couleur de l'icône : 🟡 chargement · 🟢 prêt · 🔴 enregistrement ·
🔵 transcription · ⚪ désactivée.

---

## Réglages (icône → « Réglages… »)

Tout se règle sans éditer de fichier :

- **Général** : moteur (Whisper / Parakeet), modèle, GPU/CPU, langue, micro,
  raccourci, auto-collage, volume des bips.
- **Correction** : nettoyage des hésitations, correction LLM (modèle, mode
  *conservateur* ou *light*).
- **Vocabulaire** : apprentissage automatique, récolte optionnelle dans des
  fichiers de notes, aperçu.
- **Distant** : URL et jeton du serveur (client), interface et port (serveur).

La configuration est stockée dans `config.json` (généré, ignoré par Git).
Les valeurs par défaut sont dans `griffonne/config.py`.

---

## Deux moteurs : Whisper ou Parakeet

| | **Whisper** `large-v3-turbo` (défaut) | **Parakeet** TDT 0.6B v3 |
|---|---|---|
| Précision brute (français) | ≈ égale | ≈ égale |
| Termes techniques / noms propres | ✅ meilleur : amorcé par ton vocabulaire, langue forcée | ⚠️ pas d'amorce, langue auto-détectée |
| Temps de traitement, GPU | ~0,5 s | **~0,2 s** |
| Temps de traitement, CPU | ~2,3 s (modèle `small`) | **~0,4 s** |
| Mots anglais dans du français | correct | ✅ légèrement meilleur |

Bascule : Réglages → *Moteur*, ou case « Moteur Parakeet (rapide) » dans le
menu de l'icône. Le post-traitement (hésitations, vocabulaire, LLM, collage)
est identique pour les deux.

> Parakeet en CUDA : installer `onnxruntime-gpu==1.22.0` (compilé pour
> CUDA 12 ; les versions ≥ 1.23 ciblent CUDA 13). En CPU, rien à ajouter.

---

## La correction automatique

```
Moteur (audio → texte, Whisper amorcé par le vocabulaire)
   → nettoyage : hésitations, bégaiements, remplacements déterministes
   → LLM local (Ollama) : noms propres, ponctuation, accents — sans reformuler
   → orthographe exacte du vocabulaire forcée (ex. « github » → « GitHub »)
   → collage dans l'application active
```

**Le vocabulaire se construit tout seul.** À chaque dictée, les acronymes et
termes en casse mixte sont mémorisés dans `vocabulary.json` (géré par le
programme). Ils servent ensuite à amorcer Whisper, à guider le LLM et à forcer
l'orthographe exacte. Une graine générique est fournie ; tout le reste vient
de ton usage.

Le prompt du LLM est volontairement strict (*« dans le doute, ne change
rien »*) : les tests ont montré qu'un petit modèle non contraint invente des
substitutions de noms propres.

---

## Sans GPU

Choisis le moteur **Parakeet** (préréglage `config.cpu.json`, appliqué par
`install_cpu.bat`) et désactive la correction LLM (trop lente sur CPU).
Mesures sur un Intel i7-7820X, CPU seul, ~7 s d'audio :

| Moteur | Temps |
|---|---|
| **Parakeet 0.6B** | **0,38 s** |
| Whisper `base` | 0,72 s |
| Whisper `small` | 2,14 s |
| Whisper `large-v3-turbo` | 8,11 s |

Même sans LLM, le nettoyage des hésitations et l'orthographe du vocabulaire
restent actifs. Si le téléchargement des modèles est bloqué (proxy), copie le
cache `%USERPROFILE%\.cache\huggingface\hub` depuis une autre machine : tout
fonctionne alors hors ligne.

---

## Mode distant

Un PC sans GPU peut déléguer la transcription à un PC équipé :

1. Sur le PC GPU : Réglages → Distant → définir un **jeton**, puis `serve.bat`.
2. Relier les deux machines (par ex. [Tailscale](https://tailscale.com),
   chiffré, sans ouvrir de port).
3. Sur le client : *Mode* = `remote` (ou `auto` : distant si joignable, sinon
   repli local), URL du serveur et même jeton.

L'audio est envoyé en int16 (≈ 470 Ko pour 15 s). ⚠️ Toujours définir un jeton
dès que le serveur est accessible au-delà de `localhost`. Réfléchis à la
nature des données dictées avant de les faire transiter par une autre machine.

---

## Comparaison avec murmure.app

[murmure.app](https://murmure.app) (Kieirra / Al1x-ai, AGPL v3) est un projet
indépendant qui poursuit le même objectif. Les deux
ont été comparés sur **le même corpus** : 5 phrases françaises (voix de
synthèse, 6 à 9 s), transcrites par l'API locale de murmure.app et par ce
projet, avec le taux d'erreur mot (WER) contre le texte de référence.

| | murmure.app 1.11 | Ce projet |
|---|---|---|
| Moteur | Parakeet TDT 0.6B v3 (CPU) | Whisper `large-v3-turbo` **ou** Parakeet |
| Plateformes | Windows, macOS, Linux (installeurs) | Windows (Python) |
| GPU | non utilisé pour la transcription | CUDA (Whisper et Parakeet) ou CPU |
| Correction LLM | *LLM Connect* : Ollama ou API OpenAI-compatible, prompts libres | Ollama, prompt strict intégré |
| Vocabulaire | manuel ou import `.txt` (≤ 2 mots/entrée, ≤ 100 entrées) | **appris automatiquement**, illimité |
| Hésitations | règles de formatage (regex) | intégré |
| Langue | auto-détectée (25 langues), non forçable | forçable |
| Autres | transformer un texte sélectionné, commandes vocales, micro via téléphone, API, CLI | mode distant, repli automatique |

Résultats (dictionnaire de murmure.app vide, LLM Connect non configuré) :

| Configuration | Temps moyen | WER moyen |
|---|---|---|
| murmure.app (Parakeet, CPU) | 0,51 s | 11,0 % |
| Ce projet — Whisper GPU, sans LLM | 0,59 s | 10,2 % |
| Ce projet — Whisper GPU + LLM + vocabulaire | 0,48 s | **7,0 %** |
| Ce projet — Parakeet, CPU | 0,38 s | 11,0 % |
| Ce projet — Parakeet, CUDA | 0,17 s | 11,0 % |

Lecture honnête de ces chiffres :

- **À moteur nu, égalité** : Parakeet et Whisper turbo font jeu égal sur du
  français, et Parakeet le fait avec un modèle dix fois plus petit.
- **L'écart vient du post-traitement** (LLM + vocabulaire), pas du moteur.
  murmure.app dispose d'un dictionnaire et de LLM Connect ; configurés, ils
  réduiraient l'écart.
- **Sans GPU, Parakeet est la référence** : 4 à 5 fois plus rapide que Whisper
  `small` à qualité égale. C'est pour cela qu'il est intégré ici.
- murmure.app est plus **mûr** (installeurs, multi-plateforme, communauté) et
  offre des fonctions absentes ici (transformation de texte, commandes vocales).
- Ce projet apporte le **vocabulaire auto-appris**, la **langue forçable**, le
  choix du moteur et le mode distant.

Cinq phrases en voix de synthèse : c'est indicatif, pas définitif.

---

## Dépannage

- **Rien au raccourci** : lancer en administrateur (capture clavier globale)
  ou vérifier qu'aucune autre application n'utilise le même raccourci.
- **Transcription vide** : mauvais micro (Réglages → Général → Micro).
- **Pas de correction** : Ollama absent ou modèle manquant
  (`ollama pull qwen2.5:3b`).
- **Latence anormale (~2 s de plus par dictée)** : l'URL d'Ollama doit être
  `http://127.0.0.1:11434`, pas `localhost` — sous Windows, `localhost` tente
  d'abord IPv6 alors qu'Ollama n'écoute qu'en IPv4.
- **L'app s'arrête sans raison** : consulter `griffonne_autostart.log`, chaque
  arrêt y est tracé avec sa cause.

---

## Architecture

| Fichier | Rôle |
|---|---|
| `griffonne/app.py` | Contrôleur : raccourci, capture, orchestration, rechargement |
| `griffonne/engine.py` | Moteurs Whisper (faster-whisper) et Parakeet (onnx-asr) |
| `griffonne/llm.py` | Correction par LLM local (Ollama) |
| `griffonne/clean.py` | Nettoyage déterministe, orthographe du vocabulaire |
| `griffonne/vocab_builder.py` | Vocabulaire auto-appris (+ récolte optionnelle) |
| `griffonne/backend.py` | Local / distant / auto |
| `griffonne/server.py` | Serveur de transcription distant |
| `griffonne/tray.py`, `settings_ui.py` | Icône et réglages |
| `griffonne/devices.py`, `audio.py`, `win.py` | GPU, micro, capture, fenêtre cible |

Points d'entrée : `python -m griffonne` (app), `python -m murmure.app`
(console), `python -m griffonne.server` (serveur).

---

## Licence

[MIT](LICENSE). Les modèles ont leurs propres licences : Whisper (MIT),
Parakeet (CC-BY-4.0), qwen2.5 (Apache-2.0).
