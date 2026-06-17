"""
engine.py
=========
Motor de traducción en tiempo real, controlable desde una interfaz.

- Corre en un hilo aparte con su propio loop de asyncio.
- Métodos seguros para llamar desde la GUI: start(), stop(), pause(), resume().
- Reconexión automática si la sesión Live se cae o llega a su duración máxima.
- Pausa: deja de enviar audio a Gemini (no traduce, ahorra costo) y limpia la
  cola de reproducción para no soltar audio viejo al reanudar.

Notifica a la GUI por callbacks:
    on_status(texto)          -> estado: "Conectando…", "Traduciendo", etc.
    on_transcript(lang, txt)  -> lang en {"en","es"} (o el destino), txt fragmento
"""

import asyncio
import queue
import threading

from google.genai import types

import config
from gemini_translate import build_live_config, get_client
from audio_capture import SystemCapture
from audio_playback import StreamPlayer


class TranslatorEngine:
    def __init__(self, on_status=None, on_transcript=None):
        self.on_status = on_status or (lambda s: None)
        self.on_transcript = on_transcript or (lambda lang, t: None)

        self._thread = None
        self._loop = None
        self._stop = threading.Event()
        self._paused = threading.Event()

        self.target_lang = config.TARGET_LANGUAGE
        self.out_device = None
        self.capture_device = None

        self._capture = None
        self._player = None
        self._q_out = None              # queue.Queue de bytes 24 kHz (a reproducir)
        self._tasks = []

    # ---- API pública (se llama desde la GUI) ----------------------------- #
    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self, target_lang, out_device=None, capture_device=None):
        if self.is_running():
            return
        # Espera a que un arranque anterior libere por completo los dispositivos.
        if self._thread is not None:
            self._thread.join(timeout=3)
        self.target_lang = target_lang
        self.out_device = out_device
        self.capture_device = capture_device
        self._stop.clear()
        self._paused.clear()
        self._thread = threading.Thread(target=self._thread_main, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._loop:
            self._loop.call_soon_threadsafe(self._cancel_tasks)

    def pause(self):
        self._paused.set()
        self._flush_output()
        self.on_status("Pausado")

    def resume(self):
        self._paused.clear()
        self.on_status("Traduciendo")

    def toggle_pause(self):
        if self._paused.is_set():
            self.resume()
        else:
            self.pause()

    def set_language(self, lang):
        """Cambia el idioma destino EN VIVO (sin tocar el audio): fuerza una
        reconexión y el nuevo idioma se aplica en la siguiente sesión."""
        self.target_lang = lang
        if self.is_running() and self._loop:
            self.on_status(f"Cambiando idioma a '{lang}'…")
            self._loop.call_soon_threadsafe(self._cancel_tasks)

    @property
    def paused(self):
        return self._paused.is_set()

    # ---- Interno --------------------------------------------------------- #
    def _cancel_tasks(self):
        for t in self._tasks:
            t.cancel()

    def _flush_output(self):
        if self._q_out:
            try:
                while True:
                    self._q_out.get_nowait()
            except queue.Empty:
                pass

    def _thread_main(self):
        try:
            asyncio.run(self._main())
        except Exception as e:                      # noqa: BLE001
            self.on_status(f"Error: {type(e).__name__}: {e}")

    async def _main(self):
        self._loop = asyncio.get_running_loop()
        q_in = asyncio.Queue()
        self._q_out = queue.Queue()

        try:
            client = get_client()
        except Exception as e:                      # noqa: BLE001
            self.on_status(f"Error de clave: {e}")
            return

        # Captura: el callback de PortAudio empuja a la cola asyncio.
        try:
            self._capture = SystemCapture(
                device=self.capture_device,
                sink=lambda b: self._loop.call_soon_threadsafe(q_in.put_nowait, b),
            )
            self._player = StreamPlayer(device=self.out_device)
        except Exception as e:                      # noqa: BLE001
            self.on_status(f"Error de audio: {e}")
            return

        pb_thread = threading.Thread(target=self._playback_worker, daemon=True)
        pb_thread.start()
        try:
            self._capture.start()
        except Exception as e:                      # noqa: BLE001
            self.on_status(f"Error al abrir captura: {type(e).__name__}: {e}")
            self._q_out.put(None)
            return

        # Bucle de reconexión.
        while not self._stop.is_set():
            self.on_status("Conectando…")
            try:
                cfg = build_live_config(target_language=self.target_lang)
                async with client.aio.live.connect(model=config.MODEL,
                                                   config=cfg) as session:
                    self.on_status("Traduciendo" if not self._paused.is_set()
                                   else "Pausado")
                    self._drain_async_queue(q_in)      # descarta audio viejo
                    sender = asyncio.create_task(self._sender(session, q_in))
                    receiver = asyncio.create_task(self._receiver(session))
                    self._tasks = [sender, receiver]
                    await asyncio.wait({sender, receiver},
                                       return_when=asyncio.FIRST_COMPLETED)
                    for t in self._tasks:
                        t.cancel()
            except asyncio.CancelledError:
                break
            except Exception as e:                  # noqa: BLE001
                if self._stop.is_set():
                    break
                self.on_status(f"Reconectando… ({type(e).__name__})")
                await asyncio.sleep(1.0)
                continue
            if not self._stop.is_set():
                # La sesión terminó sola (duración máxima): reconecta enseguida.
                self.on_status("Reconectando…")
                await asyncio.sleep(0.3)

        # Limpieza.
        if self._capture:
            self._capture.stop()
        self._q_out.put(None)
        pb_thread.join(timeout=2)
        self.on_status("Detenido")

    @staticmethod
    def _drain_async_queue(q):
        try:
            while True:
                q.get_nowait()
        except asyncio.QueueEmpty:
            pass

    async def _sender(self, session, q_in):
        while not self._stop.is_set():
            chunk = await q_in.get()
            if self._paused.is_set():
                continue                              # no enviar mientras pausa
            await session.send_realtime_input(
                audio=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
            )

    async def _receiver(self, session):
        async for response in session.receive():
            if self._stop.is_set():
                break
            sc = response.server_content
            if not sc:
                continue
            if self._paused.is_set():
                continue                              # ignora audio/texto en pausa
            if sc.input_transcription and sc.input_transcription.text:
                self.on_transcript("en", sc.input_transcription.text)
            if sc.output_transcription and sc.output_transcription.text:
                self.on_transcript("es", sc.output_transcription.text)
            if sc.model_turn:
                for part in sc.model_turn.parts:
                    if part.inline_data and part.inline_data.data:
                        self._q_out.put(part.inline_data.data)

    def _playback_worker(self):
        try:
            self._player.start()
        except Exception as e:                      # noqa: BLE001
            self.on_status(f"Error al abrir salida: {type(e).__name__}: {e}")
            return
        while True:
            data = self._q_out.get()
            if data is None:
                break
            try:
                self._player.write(data)
            except Exception:                         # noqa: BLE001
                pass
        self._player.stop()
