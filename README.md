# Traductor de audio del sistema EN → ES (Gemini Live)

Captura el audio que suena en tu PC (un curso en inglés) y reproduce una
traducción hablada al español casi en tiempo real, usando el modelo
`gemini-3.5-live-translate-preview`.

> 📖 **¿Primera vez? Lee el [Manual de usuario](MANUAL.md)** — instalación paso a
> paso, configuración del audio y solución de problemas, explicado desde cero.

## Estado del proyecto

- [x] **Fase 0** — Entorno + conexión a la API (`hola_mundo.py`).
- [x] **Fase 1** — Traducir un archivo WAV (EN → ES) (`gemini_translate.py`).
- [x] **Fase 2** — Capturar el audio del sistema desde CABLE Output (`audio_capture.py`).
- [x] **Fase 3** — Reproducir en un dispositivo concreto (`audio_playback.py`).
- [x] **Fase 4** — Todo en tiempo real (asyncio + colas) (`main.py`). **¡FUNCIONA!**
- [x] **Fase 5** — Interfaz gráfica (`app.py`) + motor controlable (`engine.py`):
      selección de idiomas, dispositivo de salida, Iniciar/Pausar/Detener,
      transcripción en vivo y **reconexión automática**.

## Requisitos

- Windows 11, Python 3.12 (probado).
- Clave de Gemini gratis: https://aistudio.google.com/apikey

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # y pega tu clave dentro
```

## Uso con interfaz gráfica (recomendado)

**1) Enruta el curso al cable** (así no oyes el inglés original):
   *Configuración → Sistema → Sonido → Mezclador de volumen* → tu navegador →
   **Salida = CABLE Input (VB-Audio Virtual Cable)**.
   Deja tu **dispositivo de salida predeterminado** en tus audífonos/bocinas.

**2) Abre la app:**
```powershell
python app.py
```
Elige idioma destino y dispositivo de salida, y pulsa **▶ Iniciar**.
Botones **⏸ Pausar/Reanudar** y **⏹ Detener**. Reconexión automática incluida.
(El idioma origen lo detecta el modelo solo; el selector es informativo.)

## Uso por línea de comandos (alternativa)

```powershell
python main.py                       # captura el cable, reproduce el español
python main.py --lang fr             # traducir a otro idioma (BCP-47)
python main.py --out-device "Headphones"   # forzar dispositivo de salida
python main.py --show-input          # ver también la transcripción en inglés
```
`Ctrl+C` para salir.

> El inglés se va "por dentro" al cable (no lo oyes); solo escuchas el español.
> No hay bucle porque se captura de un dispositivo (cable) y se reproduce en otro.

## Otros usos

```powershell
# Fase 0: ¿conecta la API?
python hola_mundo.py

# Fase 1: traducir un WAV de inglés a español (archivo)
python gemini_translate.py entrada_ingles.wav salida_espanol.wav

# Listar dispositivos de audio
python audio_devices.py
python audio_devices.py cable        # filtrar por nombre
```

### Generar un WAV de prueba (voz de Windows, sin instalar nada)

```powershell
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice("Microsoft Zira Desktop")   # voz en inglés (en-US)
$s.SetOutputToWaveFile("$PWD\prueba_ingles.wav")
$s.Speak("Hello, this is a test of the live translation system.")
$s.Dispose()
```

## Notas técnicas aprendidas

- El modelo de traducción es un **stream continuo**: después de que termina el
  habla, sigue emitiendo **silencio** (no manda un `turn_complete` claro). En
  modo archivo, `gemini_translate.py` detecta el fin por *inactividad de voz*
  (el silencio no cuenta) y recorta el silencio final del WAV.
- Formatos fijos de la API: entrada PCM16 **16 kHz** mono, salida PCM16
  **24 kHz** mono, chunks de **100 ms**.
- `echo_target_language=False`: en tramos que ya están en español, el modelo
  se queda callado en vez de repetirlos.
- **Host API en Windows:** se prefiere **MME** (la más compatible; auto-resamplea
  y evita el error `-9999 GetNameFromCategory` de WASAPI/WDM-KS con dispositivos
  USB). Su latencia extra es despreciable frente a Gemini.
- Las tasas se **resamplean a la tasa nativa del dispositivo**: captura → 16k,
  salida 24k → tasa del dispositivo.

## Problemas comunes

- **Error `-9999`**: dispositivo WASAPI/WDM-KS con USB. La app ya usa MME para
  evitarlo; no elijas dispositivos WDM-KS.
- **Error `-9985` (Device unavailable)**: otra app (p. ej. Zoom) tiene tomado el
  dispositivo. Usa otra salida (Speakers) o cierra/redirige la otra app.
- **Se repite/atora la traducción**: hay un eco en el ruteo de Windows. Revisa
  que NO esté activado *"Escuchar este dispositivo"* en `CABLE Output`
  (`mmsys.cpl` → Grabar) y que la fuente entre al cable por un solo camino.
- **No se oye la traducción**: la "Salida de audio" debe ser el dispositivo por
  el que realmente escuchas (audífonos/altavoces), nunca un cable.

## Archivos

| Archivo | Qué hace |
|---|---|
| `app.py` | **Interfaz gráfica** (Tkinter): idiomas, dispositivo, controles |
| `engine.py` | Motor controlable: pausa + **reconexión automática** |
| `main.py` | Traducción en tiempo real por consola (orquesta todo) |
| `config.py` | Idioma destino, formatos, dispositivos |
| `gemini_translate.py` | Conexión y streaming con Gemini (+modo archivo) |
| `audio_capture.py` | Captura del sistema (`SystemCapture`) |
| `audio_playback.py` | Reproducción (`StreamPlayer`, `play_wav`) |
| `audio_devices.py` | Listar/elegir dispositivos por nombre y Host API |
| `hola_mundo.py` | Prueba de conexión a la API |
| `.env` | `GEMINI_API_KEY` (NO se sube a git — copia de `.env.example`) |
