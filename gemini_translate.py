"""
gemini_translate.py
===================
Conexión con la Gemini Live API para traducción de voz a voz.

Fase 1: traduce un archivo WAV (inglés) -> WAV (español) para validar que la
clave, la conexión y los formatos de audio funcionan, SIN tocar todavía el
audio del sistema.

Uso:
    python gemini_translate.py entrada_ingles.wav salida_espanol.wav

Las funciones async (translate_file, etc.) se reutilizarán en la Fase 4
para el modo en tiempo real.
"""

import asyncio
import os
import sys
import time
import wave

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from dotenv import load_dotenv

from google import genai
from google.genai import types

import config

load_dotenv()

# La consola de Windows usa cp1252 y truena con acentos/emojis. Forzamos UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# --------------------------------------------------------------------------- #
#  Utilidades de audio
# --------------------------------------------------------------------------- #
def wav_to_input_chunks(path, target_rate=config.INPUT_SAMPLE_RATE,
                        chunk_bytes=config.INPUT_CHUNK_BYTES):
    """
    Lee cualquier WAV/FLAC, lo convierte a PCM16 mono al sample rate destino
    y devuelve una lista de trozos (bytes) listos para enviar a Gemini.
    """
    data, src_rate = sf.read(path, dtype="float64", always_2d=True)

    # Estéreo -> mono (promedio de canales)
    mono = data.mean(axis=1)

    # Resampleo a 16 kHz si hace falta
    if src_rate != target_rate:
        g = np.gcd(int(src_rate), int(target_rate))
        mono = resample_poly(mono, target_rate // g, src_rate // g)

    # Float [-1, 1] -> PCM16 little-endian
    mono = np.clip(mono, -1.0, 1.0)
    pcm16 = (mono * 32767.0).astype("<i2").tobytes()

    # Trocear en chunks de 100 ms
    chunks = [pcm16[i:i + chunk_bytes] for i in range(0, len(pcm16), chunk_bytes)]
    return chunks


def trim_trailing_silence(pcm_bytes, rate=config.OUTPUT_SAMPLE_RATE,
                          threshold=0.01, keep_ms=300):
    """Recorta el silencio del final. Deja `keep_ms` de cola para no cortar brusco."""
    samples = np.frombuffer(pcm_bytes, dtype="<i2").astype(np.float32) / 32768.0
    if samples.size == 0:
        return pcm_bytes
    win = max(1, int(rate * 0.05))  # ventanas de 50 ms
    last_voice = 0
    for i in range(0, len(samples), win):
        seg = samples[i:i + win]
        if np.sqrt(np.mean(seg ** 2)) > threshold:
            last_voice = i + len(seg)
    end = min(len(samples), last_voice + int(rate * keep_ms / 1000))
    return (samples[:end] * 32767).astype("<i2").tobytes()


def write_output_wav(path, pcm_bytes, rate=config.OUTPUT_SAMPLE_RATE):
    """Guarda bytes PCM16 mono como WAV."""
    with wave.open(path, "wb") as w:
        w.setnchannels(config.CHANNELS)
        w.setsampwidth(config.SAMPLE_WIDTH)
        w.setframerate(rate)
        w.writeframes(pcm_bytes)


def build_live_config(target_language=None, echo=None):
    """Configuración de la sesión Live para traducción.
    target_language: código BCP-47 (None usa config.TARGET_LANGUAGE)."""
    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        translation_config=types.TranslationConfig(
            target_language_code=target_language or config.TARGET_LANGUAGE,
            echo_target_language=config.ECHO_TARGET_LANGUAGE if echo is None
            else echo,
        ),
    )


def get_client():
    from apikey import load_api_key
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError(
            "Falta GEMINI_API_KEY. Configúrala en la app o copia .env.example a "
            ".env y pega tu clave (https://aistudio.google.com/apikey)."
        )
    return genai.Client(api_key=api_key)


# --------------------------------------------------------------------------- #
#  Fase 1: traducir un archivo
# --------------------------------------------------------------------------- #
async def translate_file(input_wav, output_wav, pace=True):
    """
    Envía un WAV a Gemini y guarda la traducción hablada como WAV.
    Imprime las transcripciones (origen y destino) en consola.
    """
    chunks = wav_to_input_chunks(input_wav)
    print(f"[i] Entrada: {input_wav} -> {len(chunks)} chunks de "
          f"{config.CHUNK_MS} ms ({len(chunks) * config.CHUNK_MS / 1000:.1f} s)")

    client = get_client()
    out_audio = bytearray()
    input_done = asyncio.Event()
    last_audio = [time.monotonic()]   # mutable para compartir entre tareas
    SILENCE_TIMEOUT = 2.5             # s sin audio nuevo (tras fin de entrada) = fin

    async with client.aio.live.connect(model=config.MODEL,
                                        config=build_live_config()) as session:

        async def send():
            for chunk in chunks:
                await session.send_realtime_input(
                    audio=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                )
                # Pacing a tiempo real para imitar el streaming en vivo.
                if pace:
                    await asyncio.sleep(config.CHUNK_MS / 1000)
            # Marca fin del audio de entrada (si el SDK lo soporta).
            try:
                await session.send_realtime_input(audio_stream_end=True)
            except TypeError:
                pass
            input_done.set()

        async def recv():
            async for response in session.receive():
                sc = response.server_content
                if not sc:
                    continue
                if sc.input_transcription and sc.input_transcription.text:
                    print(f"  EN: {sc.input_transcription.text}", flush=True)
                if sc.output_transcription and sc.output_transcription.text:
                    print(f"  ES: {sc.output_transcription.text}", flush=True)
                if sc.model_turn:
                    for part in sc.model_turn.parts:
                        if part.inline_data and part.inline_data.data:
                            data = part.inline_data.data
                            out_audio.extend(data)
                            # Solo el audio CON VOZ reinicia el watchdog; el modelo
                            # emite silencio continuo y eso no cuenta como "actividad".
                            arr = np.frombuffer(data, dtype="<i2")
                            if arr.size and \
                                    np.sqrt(np.mean(arr.astype(np.float32) ** 2)) > 100:
                                last_audio[0] = time.monotonic()
                # El modelo cerró el turno y ya enviamos toda la entrada.
                done = getattr(sc, "turn_complete", False) or \
                    getattr(sc, "generation_complete", False)
                if done and input_done.is_set():
                    break

        async def watchdog():
            # Si tras terminar la entrada no llega audio por SILENCE_TIMEOUT,
            # asumimos que la traducción terminó (por si no llega turn_complete).
            await input_done.wait()
            while True:
                await asyncio.sleep(0.3)
                if time.monotonic() - last_audio[0] > SILENCE_TIMEOUT:
                    return

        send_task = asyncio.create_task(send())
        recv_task = asyncio.create_task(recv())
        await send_task
        last_audio[0] = time.monotonic()  # reinicia el reloj al cerrar la entrada
        wd_task = asyncio.create_task(watchdog())
        # Termina cuando el modelo cierre el turno O cuando el watchdog detecte
        # silencio prolongado, lo que pase primero. Tope duro de seguridad: 60 s.
        done, pending = await asyncio.wait(
            {recv_task, wd_task},
            timeout=60,
            return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()

    if not out_audio:
        print("[!] No se recibió audio traducido. Revisa la clave/modelo/conexión.")
        return False

    audio = trim_trailing_silence(bytes(out_audio))
    write_output_wav(output_wav, audio)
    secs = len(audio) / (config.OUTPUT_SAMPLE_RATE * config.SAMPLE_WIDTH)
    print(f"[ok] Traducción guardada: {output_wav} ({secs:.1f} s de audio en "
          f"{config.TARGET_LANGUAGE})")
    return True


def main():
    if len(sys.argv) != 3:
        print("Uso: python gemini_translate.py <entrada.wav> <salida.wav>")
        sys.exit(1)
    asyncio.run(translate_file(sys.argv[1], sys.argv[2]))


if __name__ == "__main__":
    main()
