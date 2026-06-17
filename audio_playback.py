"""
audio_playback.py
================
Fase 3: reproducir audio en un dispositivo concreto (tus audífonos),
distinto del de captura, para no crear un bucle.

    python audio_playback.py archivo.wav                 # dispositivo por defecto
    python audio_playback.py archivo.wav "CABLE Input"   # a un dispositivo por nombre

`play_wav` es para probar; `StreamPlayer` (clase) es el reproductor de streaming
que usará la Fase 4 con el audio a 24 kHz que devuelve Gemini.
"""

import sys

import numpy as np
import soundfile as sf
import sounddevice as sd
from scipy.signal import resample_poly

import config
from audio_devices import find_device


def _device_rate(device):
    """Tasa de muestreo nativa del dispositivo (o None si es el predeterminado)."""
    if device is None:
        return None
    return int(sd.query_devices(device)["default_samplerate"])


def _resample_mono(arr_float, src_rate, dst_rate):
    if src_rate == dst_rate:
        return arr_float
    g = np.gcd(int(src_rate), int(dst_rate))
    return resample_poly(arr_float, dst_rate // g, src_rate // g)


def _resolve_output_device(device):
    if device is None:
        device = config.PLAYBACK_DEVICE
    if isinstance(device, str):
        device = find_device(device, "output")
    return device  # None = dispositivo de salida por defecto de Windows


def play_wav(path, device=None):
    """Reproduce un WAV completo (bloqueante) en el dispositivo dado.
    Resamplea a la tasa nativa del dispositivo (WASAPI no convierte solo)."""
    device = _resolve_output_device(device)
    data, rate = sf.read(path, dtype="float32")
    if data.ndim > 1:                      # a mono
        data = data.mean(axis=1)
    dev_rate = _device_rate(device)
    if dev_rate and dev_rate != rate:
        data = _resample_mono(data, rate, dev_rate)
        rate = dev_rate
    name = sd.query_devices(device)["name"].strip() if device is not None \
        else "predeterminado"
    print(f"[i] Reproduciendo {path} en [{device}] {name} @ {rate} Hz")
    sd.play(data, rate, device=device)
    sd.wait()
    print("[ok] Reproducción terminada")


class StreamPlayer:
    """
    Reproductor de streaming para la Fase 4.
    Recibe bytes PCM16 mono (a OUTPUT_SAMPLE_RATE) vía write() y los reproduce
    de forma continua en el dispositivo elegido.
    """

    def __init__(self, device=None, rate=config.OUTPUT_SAMPLE_RATE):
        self.device = _resolve_output_device(device)
        self.in_rate = rate                       # 24000 Hz que manda Gemini
        self.dev_rate = _device_rate(self.device) or rate
        self._stream = sd.RawOutputStream(
            samplerate=self.dev_rate, channels=config.CHANNELS,
            dtype="int16", device=self.device,
        )

    def start(self):
        self._stream.start()
        return self

    def write(self, pcm_bytes):
        """Encola bytes PCM16 (a 24 kHz) para reproducir, resampleando al
        ritmo del dispositivo si hace falta."""
        if self.dev_rate != self.in_rate:
            arr = np.frombuffer(pcm_bytes, dtype="<i2").astype(np.float32)
            arr = _resample_mono(arr, self.in_rate, self.dev_rate)
            pcm_bytes = np.clip(arr, -32768, 32767).astype("<i2").tobytes()
        self._stream.write(pcm_bytes)

    def stop(self):
        self._stream.stop()
        self._stream.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python audio_playback.py <archivo.wav> [nombre_dispositivo]")
        sys.exit(1)
    dev = sys.argv[2] if len(sys.argv) > 2 else None
    play_wav(sys.argv[1], dev)
