"""
main.py — Fase 4
================
Traducción de voz en TIEMPO REAL del audio del sistema.

Tubería con 3 etapas concurrentes:
  A) Captura  (SystemCapture): CABLE Output -> chunks 16 kHz -> cola de entrada
  B) Gemini   (asyncio): envía la entrada y recibe audio español 24 kHz
  C) Reproduce (StreamPlayer en un hilo): cola de salida -> audífonos

Uso normal:
    python main.py
    python main.py --lang es           # cambiar idioma destino
    python main.py --out-device "Speakers"

Requisito: el curso/navegador debe estar enrutado a "CABLE Input"
(Configuración > Sonido > Mezclador de volumen). Así no oyes el inglés
original (se va al cable) y solo escuchas el español por tu salida normal.

Ctrl+C para salir.
"""

import argparse
import asyncio
import queue
import sys
import threading
import wave

from google.genai import types

import config
from gemini_translate import build_live_config, get_client
from audio_capture import SystemCapture
from audio_playback import StreamPlayer

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


async def run_realtime(out_device=None, play=True, save_path=None,
                       duration=None, show_input=False):
    """
    Corre la tubería en tiempo real.
      out_device : dispositivo de salida (None = predeterminado de Windows)
      play       : si False, no reproduce (solo guarda) — útil para pruebas
      save_path  : si se da, además guarda el audio traducido como WAV
      duration   : segundos a correr (None = hasta Ctrl+C)
      show_input : imprimir también la transcripción en inglés
    """
    client = get_client()
    loop = asyncio.get_running_loop()
    q_in = asyncio.Queue()      # bytes PCM16 16 kHz (captura -> Gemini)
    q_out = queue.Queue()       # bytes PCM16 24 kHz (Gemini -> reproducción)
    stop = asyncio.Event()
    saved = bytearray()

    # Captura: el callback (hilo de PortAudio) empuja a la cola asyncio.
    capture = SystemCapture(
        sink=lambda b: loop.call_soon_threadsafe(q_in.put_nowait, b)
    )

    # Hilo de reproducción: consume q_out y lo escribe en el dispositivo.
    player = StreamPlayer(device=out_device) if play else None

    def playback_worker():
        if player:
            player.start()
        while True:
            data = q_out.get()
            if data is None:
                break
            if save_path:
                saved.extend(data)
            if player:
                try:
                    player.write(data)
                except Exception:
                    pass
        if player:
            player.stop()

    pb_thread = threading.Thread(target=playback_worker, daemon=True)

    print(f"[i] Idioma destino: {config.TARGET_LANGUAGE}")
    print(f"[i] Captura: CABLE Output  |  Salida: "
          f"{'(ninguna)' if not play else (out_device or 'predeterminada')}")
    print("[i] Enruta el curso a 'CABLE Input'. Habla/reproduce y espera "
          "unos segundos.\n[i] Ctrl+C para salir.\n")

    async with client.aio.live.connect(model=config.MODEL,
                                        config=build_live_config()) as session:
        pb_thread.start()
        capture.start()

        async def sender():
            while not stop.is_set():
                chunk = await q_in.get()
                await session.send_realtime_input(
                    audio=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                )

        async def receiver():
            async for response in session.receive():
                sc = response.server_content
                if not sc:
                    continue
                if show_input and sc.input_transcription \
                        and sc.input_transcription.text:
                    print(f"\n[EN] {sc.input_transcription.text}", flush=True)
                if sc.output_transcription and sc.output_transcription.text:
                    print(sc.output_transcription.text, end="", flush=True)
                if sc.model_turn:
                    for part in sc.model_turn.parts:
                        if part.inline_data and part.inline_data.data:
                            q_out.put(part.inline_data.data)
                if stop.is_set():
                    break

        send_task = asyncio.create_task(sender())
        recv_task = asyncio.create_task(receiver())

        try:
            if duration:
                await asyncio.sleep(duration)
            else:
                # Corre hasta que una tarea termine (error/desconexión) o Ctrl+C.
                await asyncio.wait({send_task, recv_task},
                                   return_when=asyncio.FIRST_COMPLETED)
        finally:
            stop.set()
            for t in (send_task, recv_task):
                t.cancel()
            capture.stop()
            q_out.put(None)        # detiene el hilo de reproducción
            pb_thread.join(timeout=2)

    if save_path and saved:
        with wave.open(save_path, "wb") as w:
            w.setnchannels(config.CHANNELS)
            w.setsampwidth(config.SAMPLE_WIDTH)
            w.setframerate(config.OUTPUT_SAMPLE_RATE)
            w.writeframes(bytes(saved))
        print(f"\n[ok] Audio traducido guardado en {save_path} "
              f"({len(saved)/(config.OUTPUT_SAMPLE_RATE*2):.1f}s)")


def main():
    ap = argparse.ArgumentParser(description="Traductor de audio en tiempo real")
    ap.add_argument("--lang", help="idioma destino (BCP-47), p.ej. es, en, fr")
    ap.add_argument("--out-device", help="nombre del dispositivo de salida")
    ap.add_argument("--show-input", action="store_true",
                    help="mostrar también la transcripción en inglés")
    args = ap.parse_args()

    if args.lang:
        config.TARGET_LANGUAGE = args.lang

    try:
        asyncio.run(run_realtime(out_device=args.out_device,
                                 show_input=args.show_input))
    except KeyboardInterrupt:
        print("\n[i] Saliendo. ¡Listo!")


if __name__ == "__main__":
    main()
