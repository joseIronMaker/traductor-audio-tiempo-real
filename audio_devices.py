"""
audio_devices.py
================
Utilidades para listar y encontrar dispositivos de audio.

    python audio_devices.py            # lista todo
    python audio_devices.py cable      # busca dispositivos cuyo nombre contenga "cable"
"""

import sys
import sounddevice as sd


def list_devices():
    """Imprime entradas (captura) y salidas (reproducción) con su índice."""
    devs = sd.query_devices()
    print("=== ENTRADAS (captura) ===")
    for i, d in enumerate(devs):
        if d["max_input_channels"] > 0:
            print(f"  [{i:2}] {d['name']}  "
                  f"({d['max_input_channels']} ch, {int(d['default_samplerate'])} Hz)")
    print("=== SALIDAS (reproducción) ===")
    for i, d in enumerate(devs):
        if d["max_output_channels"] > 0:
            print(f"  [{i:2}] {d['name']}  "
                  f"({d['max_output_channels']} ch, {int(d['default_samplerate'])} Hz)")


# Preferencia de Host API en Windows: MME primero (la más compatible, auto-
# resamplea y evita el error -9999 de WASAPI/WDM-KS con dispositivos USB),
# luego WASAPI, DirectSound y WDM-KS al final (exclusiva/frágil).
# La latencia extra de MME (~decenas de ms) es despreciable frente a Gemini.
_HOSTAPI_PRIORITY = ["MME", "Windows WASAPI", "Windows DirectSound", "Windows WDM-KS"]


def find_device(name_substring, kind="input"):
    """
    Devuelve el índice del dispositivo cuyo nombre contenga `name_substring`.
    kind = "input" o "output". Windows expone el mismo dispositivo por varias
    APIs; se prefiere WASAPI, luego MME, etc., y como desempate los de 2 canales.
    Lanza error si no encuentra ninguno.
    """
    key = "max_input_channels" if kind == "input" else "max_output_channels"
    name_substring = name_substring.lower()
    hostapis = sd.query_hostapis()
    matches = [(i, d) for i, d in enumerate(sd.query_devices())
               if d[key] > 0 and name_substring in d["name"].lower()]
    if not matches:
        raise RuntimeError(
            f"No se encontró un dispositivo de {kind} que contenga "
            f"'{name_substring}'. Corre 'python audio_devices.py' para ver los "
            f"disponibles."
        )

    def rank(item):
        i, d = item
        api_name = hostapis[d["hostapi"]]["name"]
        api_rank = _HOSTAPI_PRIORITY.index(api_name) \
            if api_name in _HOSTAPI_PRIORITY else len(_HOSTAPI_PRIORITY)
        ch = d[key]
        ch_rank = 0 if ch == 2 else 1 if ch == 1 else 2
        return (api_rank, ch_rank, i)

    matches.sort(key=rank)
    return matches[0][0]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        q = sys.argv[1].lower()
        print(f"Dispositivos que contienen '{q}':")
        for i, d in enumerate(sd.query_devices()):
            if q in d["name"].lower():
                io = []
                if d["max_input_channels"] > 0:
                    io.append("ENTRADA")
                if d["max_output_channels"] > 0:
                    io.append("SALIDA")
                print(f"  [{i:2}] {d['name']}  -> {', '.join(io)}")
    else:
        list_devices()
