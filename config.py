"""
Configuración central del traductor.
Aquí cambias idioma destino, formatos de audio y (más adelante) dispositivos.
"""

# --- Modelo Gemini ---
MODEL = "gemini-3.5-live-translate-preview"

# --- Idioma destino (código BCP-47) ---
# "es" = español, "en" = inglés, "fr" = francés, "pt" = portugués, etc.
TARGET_LANGUAGE = "es"

# Si True: cuando el audio de entrada YA está en el idioma destino, el modelo
# repite ("echo") ese audio. Si False: se queda callado en esos tramos.
# Para un curso 100% en inglés cualquiera sirve; False evita ruido raro.
ECHO_TARGET_LANGUAGE = False

# --- Formatos de audio (fijados por la API, no cambiar) ---
INPUT_SAMPLE_RATE = 16000   # Hz, lo que ESPERA Gemini a la entrada
OUTPUT_SAMPLE_RATE = 24000  # Hz, lo que DEVUELVE Gemini
CHANNELS = 1                # mono
SAMPLE_WIDTH = 2            # bytes (PCM 16-bit)
CHUNK_MS = 100              # tamaño de cada trozo enviado, en milisegundos

# Muestras y bytes por chunk de entrada (16 kHz, mono, 16-bit)
INPUT_CHUNK_SAMPLES = INPUT_SAMPLE_RATE * CHUNK_MS // 1000   # 1600
INPUT_CHUNK_BYTES = INPUT_CHUNK_SAMPLES * SAMPLE_WIDTH       # 3200

# --- Dispositivos (se usan desde la Fase 3/4; None = predeterminado) ---
CAPTURE_DEVICE = None   # de dónde se captura el audio del sistema
PLAYBACK_DEVICE = None  # por dónde sale la traducción (audífonos)
