"""
audio_capture.py
===============
Fase 2: capturar el audio del sistema.

Con VB-CABLE, el audio del curso entra a "CABLE Input" y nosotros lo leemos
desde "CABLE Output" (que Windows expone como un dispositivo de grabación).
Así no necesitamos WASAPI loopback.

    python audio_capture.py captura.wav 10   # graba 10 s de CABLE Output

`record_to_wav` es para probar; `SystemCapture` (clase) es el motor de streaming
que usará la Fase 4 en tiempo real.
"""

import queue
import sys

import numpy as np
import soundfile as sf
import sounddevice as sd
from scipy.signal import resample_poly

import config
from audio_devices import find_device


def _resolve_capture_device(device):
    if device is None:
        device = config.CAPTURE_DEVICE
    if device is None:
        device = find_device("CABLE Output", "input")
    elif isinstance(device, str):
        device = find_device(device, "input")
    return device


def _to_mono16k(block_int16, native_rate, channels,
                target_rate=config.INPUT_SAMPLE_RATE):
    """(frames, channels) int16 -> bytes PCM16 mono a 16 kHz."""
    data = block_int16.astype(np.float32) / 32768.0
    mono = data.mean(axis=1) if channels > 1 else data.reshape(-1)
    if native_rate != target_rate:
        g = np.gcd(int(native_rate), int(target_rate))
        mono = resample_poly(mono, target_rate // g, native_rate // g)
    return (np.clip(mono, -1.0, 1.0) * 32767).astype("<i2").tobytes()


def record_to_wav(out_path, seconds=10, device=None,
                  target_rate=config.INPUT_SAMPLE_RATE):
    """Graba `seconds` del dispositivo de captura y guarda WAV mono 16 kHz."""
    device = _resolve_capture_device(device)
    info = sd.query_devices(device)
    native_rate = int(info["default_samplerate"])
    channels = min(2, info["max_input_channels"])
    print(f"[i] Capturando de [{device}] {info['name'].strip()} "
          f"@ {native_rate} Hz, {channels} ch, {seconds}s")

    rec = sd.rec(int(native_rate * seconds), samplerate=native_rate,
                 channels=channels, dtype="int16", device=device)
    sd.wait()

    pcm = _to_mono16k(rec, native_rate, channels, target_rate)
    arr = np.frombuffer(pcm, dtype="<i2")
    sf.write(out_path, arr, target_rate, subtype="PCM_16")
    rms = float(np.sqrt(np.mean((arr.astype(np.float32) / 32768.0) ** 2)))
    print(f"[ok] {out_path}  ({len(arr) / target_rate:.1f}s, RMS={rms:.4f})")
    if rms < 0.001:
        print("[!] RMS casi cero: probablemente no había audio sonando, o el "
              "curso no está enrutado a CABLE Input.")
    return rms


class SystemCapture:
    """
    Motor de captura en streaming para la Fase 4.
    Abre un InputStream y va dejando chunks de PCM16 mono 16 kHz (bytes) en
    una cola thread-safe. El callback corre en un hilo de PortAudio.
    """

    def __init__(self, device=None, target_rate=config.INPUT_SAMPLE_RATE,
                 sink=None):
        self.device = _resolve_capture_device(device)
        info = sd.query_devices(self.device)
        self.native_rate = int(info["default_samplerate"])
        self.channels = min(2, info["max_input_channels"])
        self.target_rate = target_rate
        self.q = queue.Queue()
        # sink: función que recibe cada chunk (bytes). Por defecto, a la cola.
        # En la Fase 4 se pasa un sink que reenvía a la cola de asyncio.
        self.sink = sink if sink is not None else self.q.put
        self._stream = None
        # blocksize = 100 ms de muestras al ritmo nativo
        self.blocksize = int(self.native_rate * config.CHUNK_MS / 1000)

    def _callback(self, indata, frames, time_info, status):
        if status:
            # underrun/overflow ocasional; no es fatal
            pass
        self.sink(_to_mono16k(indata.copy(), self.native_rate,
                              self.channels, self.target_rate))

    def start(self):
        self._stream = sd.InputStream(
            samplerate=self.native_rate, channels=self.channels,
            dtype="int16", device=self.device, blocksize=self.blocksize,
            callback=self._callback,
        )
        self._stream.start()
        return self

    def stop(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "captura.wav"
    secs = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    record_to_wav(out, secs)
