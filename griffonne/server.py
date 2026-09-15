"""Serveur de transcription distant — à lancer sur le PC équipé du GPU.

Reçoit l'audio brut (float32 mono 16 kHz) en POST /transcribe, renvoie le texte
final (transcrit + corrigé) en JSON. Authentification par jeton partagé.

Lancement :  python -m griffonne.server     (ou serve.bat)
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

from . import config, vocab_builder
from .backend import LocalBackend


def _make_handler(backend: LocalBackend, token: str):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, obj: dict) -> None:
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                self._send(200, {"status": "ok", "device": backend.device})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):  # noqa: N802
            if self.path != "/transcribe":
                self._send(404, {"error": "not found"})
                return
            if token and self.headers.get("X-Token") != token:
                self._send(401, {"error": "unauthorized"})
                return
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n) if n else b""
            # int16 par défaut côté client récent ; float32 accepté (compat.)
            if self.headers.get("X-Audio-Format") == "pcm_s16le":
                audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio = np.frombuffer(raw, dtype=np.float32)
            try:
                text = backend.process(audio)
            except Exception as exc:  # noqa: BLE001
                self._send(500, {"error": repr(exc)})
                return
            self._send(200, {"text": text})

        def log_message(self, *args):  # silencieux
            return

    return Handler


def main() -> None:
    cfg = config.load()
    print("[server] construction du vocabulaire...")
    vocab = vocab_builder.build(cfg)
    print(f"[server] chargement du backend ({cfg['model']})...")
    backend = LocalBackend(cfg, vocab)
    backend.warmup()

    handler = _make_handler(backend, cfg["remote_token"])
    srv = ThreadingHTTPServer((cfg["server_host"], cfg["server_port"]), handler)
    print(f"[server] PRÊT — écoute sur {cfg['server_host']}:{cfg['server_port']} "
          f"(device {backend.device})")
    if not cfg["remote_token"]:
        print("[server] ⚠️  AUCUN JETON défini : n'expose ce port que sur un "
              "réseau de confiance (ex. Tailscale). Définis 'remote_token'.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] arrêt.")
        srv.shutdown()


if __name__ == "__main__":
    main()
