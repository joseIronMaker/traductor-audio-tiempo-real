"""
apikey.py
=========
Carga y guarda la clave de Gemini de forma robusta, para que el programa
funcione tanto como script (.env) como empaquetado en un .exe instalado.

Orden de búsqueda:
  1. Variable de entorno GEMINI_API_KEY
  2. Archivo .env en el directorio actual / junto al ejecutable
  3. Archivo settings.env en la carpeta APPDATA del usuario

Si no hay clave, la GUI la pide y la guarda en (3).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

APP_NAME = "TraductorAudioGemini"


def settings_path():
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / APP_NAME / "settings.env"


def load_api_key():
    """Devuelve la clave si la encuentra, o None."""
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"].strip()

    # .env del directorio actual / junto al ejecutable
    load_dotenv()
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"].strip()

    # settings.env en APPDATA
    p = settings_path()
    if p.exists():
        load_dotenv(p)
        if os.environ.get("GEMINI_API_KEY"):
            return os.environ["GEMINI_API_KEY"].strip()

    return None


def save_api_key(key):
    """Guarda la clave en %APPDATA% y la deja activa en este proceso."""
    key = key.strip()
    p = settings_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"GEMINI_API_KEY={key}\n", encoding="utf-8")
    os.environ["GEMINI_API_KEY"] = key
    return p
