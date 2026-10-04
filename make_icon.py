"""Génère assets/griffonne.ico (icône de l'application) — reproductible.

Usage : python make_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

BG = (46, 125, 90)        # vert Griffonne (même teinte que l'icône « prêt »)
FG = (255, 255, 255, 240)
S = 1024                  # rendu haute résolution, réduit ensuite (LANCZOS)


def render(size: int = S) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = size / 1024

    d.ellipse((0, 0, size, size), fill=BG)                       # pastille
    # capsule du micro
    d.rounded_rectangle((396 * k, 210 * k, 628 * k, 600 * k),
                        radius=116 * k, fill=FG)
    # arceau
    d.arc((318 * k, 360 * k, 706 * k, 726 * k), start=0, end=180,
          fill=FG, width=int(52 * k))
    # pied + socle
    d.rounded_rectangle((486 * k, 700 * k, 538 * k, 812 * k),
                        radius=26 * k, fill=FG)
    d.rounded_rectangle((386 * k, 790 * k, 638 * k, 842 * k),
                        radius=26 * k, fill=FG)
    return img


def main() -> None:
    out = Path(__file__).parent / "assets"
    out.mkdir(exist_ok=True)
    base = render().resize((256, 256), Image.LANCZOS)
    ico = out / "griffonne.ico"
    base.save(ico, format="ICO",
              sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                     (128, 128), (256, 256)])
    base.save(out / "griffonne.png")
    print(f"icône générée : {ico} ({ico.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
