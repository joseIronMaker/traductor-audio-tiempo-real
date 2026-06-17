"""Genera icon.ico e icon.png: audífonos sobre fondo degradado indigo con
un punto verde de 'en vivo'. Ejecuta: python make_icon.py"""
from PIL import Image, ImageDraw

S = 1024
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# --- Fondo con degradado vertical ---
grad = Image.new("RGB", (S, S))
gd = ImageDraw.Draw(grad)
top, bot = (99, 102, 241), (55, 48, 163)   # indigo claro -> oscuro
for y in range(S):
    t = y / (S - 1)
    gd.line([(0, y), (S, y)], fill=(
        int(top[0] * (1 - t) + bot[0] * t),
        int(top[1] * (1 - t) + bot[1] * t),
        int(top[2] * (1 - t) + bot[2] * t)))

mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1],
                                       radius=int(S * 0.22), fill=255)
img.paste(grad, (0, 0), mask)

d = ImageDraw.Draw(img)
white = (255, 255, 255, 255)
cx = S / 2

# --- Diadema (banda superior) ---
bw = S * 0.52
band_top = S * 0.30
d.arc([cx - bw / 2, band_top, cx + bw / 2, band_top + bw], 180, 360,
      fill=white, width=int(S * 0.06))

# --- Auriculares (a los extremos de la banda) ---
ear_w, ear_h = S * 0.14, S * 0.22
ey = band_top + bw / 2
for ex in (cx - bw / 2, cx + bw / 2):
    d.rounded_rectangle([ex - ear_w / 2, ey, ex + ear_w / 2, ey + ear_h],
                        radius=int(ear_w * 0.4), fill=white)

# --- Punto verde "en vivo" ---
r = S * 0.07
gx, gy = S * 0.75, S * 0.25
d.ellipse([gx - r, gy - r, gx + r, gy + r], fill=(34, 197, 94, 255))

img = img.resize((256, 256), Image.LANCZOS)
img.save("icon.png")
img.save("icon.ico", sizes=[(256, 256), (128, 128), (64, 64),
                            (48, 48), (32, 32), (16, 16)])
print("Listo: icon.png e icon.ico")
