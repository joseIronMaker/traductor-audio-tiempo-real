"""
Fase 0 — Prueba de conexión ("hola mundo").
Verifica que la clave funciona y que se puede abrir una sesión Live,
sin enviar audio todavía.

    python hola_mundo.py
"""

import asyncio
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

import config

load_dotenv()


async def main():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("[X] Falta GEMINI_API_KEY en .env")
        return
    print(f"[i] Clave detectada (termina en ...{key[-6:]})")
    print(f"[i] Modelo: {config.MODEL}")

    client = genai.Client(api_key=key)
    cfg = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        translation_config=types.TranslationConfig(
            target_language_code=config.TARGET_LANGUAGE,
            echo_target_language=config.ECHO_TARGET_LANGUAGE,
        ),
    )

    try:
        async with client.aio.live.connect(model=config.MODEL, config=cfg):
            print("[ok] Conexión con la Live API establecida. Todo en orden.")
    except Exception as e:
        print(f"[X] No se pudo conectar: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
