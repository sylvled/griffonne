"""Sortie du texte transcrit : presse-papier + auto-collage optionnel.
Utilise pynput (et non `keyboard`) qui ne bloque pas les touches."""
import time

import pyperclip
from pynput.keyboard import Controller, Key

_kb = Controller()


def output_text(text: str, auto_paste: bool = True) -> None:
    if not text:
        return
    pyperclip.copy(text)
    if auto_paste:
        # petit délai pour laisser le presse-papier se mettre à jour
        time.sleep(0.08)
        with _kb.pressed(Key.ctrl):
            _kb.press("v")
            _kb.release("v")
