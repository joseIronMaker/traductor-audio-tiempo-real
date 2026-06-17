# 📖 Manual de usuario — Traductor de audio en tiempo real

Traduce **lo que suena en tu computadora** (un curso, una reunión, un video) a
otro idioma y lo escuchas hablado casi al instante, con subtítulos en vivo.
Usa el modelo **Gemini 3.5 Live Translate** de Google.

> Ejemplo: un curso de Udemy en inglés → lo oyes en español mientras lo ves.

---

## 🧭 Índice
1. [¿Qué necesito? (requisitos)](#1-qué-necesito-requisitos)
2. [Instalación paso a paso](#2-instalación-paso-a-paso)
3. [Configurar el audio (lo más importante)](#3-configurar-el-audio-lo-más-importante)
4. [Usar la aplicación](#4-usar-la-aplicación)
5. [Casos de uso (YouTube, Zoom, Udemy…)](#5-casos-de-uso)
6. [Problemas comunes y soluciones](#6-problemas-comunes-y-soluciones)
7. [Preguntas frecuentes](#7-preguntas-frecuentes)

---

## 1. ¿Qué necesito? (requisitos)

| Necesitas | Para qué | Costo |
|---|---|---|
| **Windows 10 u 11** | Sistema operativo | — |
| **Python 3.10 o superior** | Ejecutar el programa | Gratis |
| **VB-CABLE** | "Cable" de audio virtual para capturar el sonido | Gratis |
| **Clave de Gemini (API key)** | Conectar con el traductor de Google | Gratis (con tier de prueba) |
| **Audífonos o bocinas** | Escuchar la traducción | — |
| **Internet** | La traducción ocurre en la nube | — |

---

## 2. Instalación paso a paso

### Paso 2.1 — Instalar Python
1. Descarga Python desde **https://www.python.org/downloads/**
2. Ejecuta el instalador y **marca la casilla "Add Python to PATH"** (¡importante!).
3. Clic en **Install Now**.

Para verificar, abre **PowerShell** y escribe:
```powershell
python --version
```
Debe mostrar algo como `Python 3.12.x`.

### Paso 2.2 — Instalar VB-CABLE (el cable de audio)
1. Ve a **https://vb-audio.com/Cable** y descarga el paquete (botón *Download*).
2. Descomprime el ZIP.
3. **Clic derecho** en `VBCABLE_Setup_x64.exe` → **Ejecutar como administrador**.
4. Clic en **Install Driver** y **reinicia** la computadora.

> Esto agrega dos dispositivos: **CABLE Input** (entrada) y **CABLE Output** (salida).
> Es seguro y se desinstala corriendo el mismo instalador → *Remove Driver*.

### Paso 2.3 — Descargar el programa
**Opción fácil (sin Git):**
1. Entra a **https://github.com/joseIronMaker/traductor-audio-tiempo-real**
2. Botón verde **Code** → **Download ZIP**.
3. Descomprime la carpeta donde quieras (ej. el Escritorio).

**Opción con Git:**
```powershell
git clone https://github.com/joseIronMaker/traductor-audio-tiempo-real.git
```

### Paso 2.4 — Instalar las dependencias
Abre **PowerShell dentro de la carpeta del programa** (clic derecho en la
carpeta → *Abrir en Terminal*), y ejecuta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> ⚠️ Si al activar sale un error de "ejecución de scripts deshabilitada", corre
> esto una vez y vuelve a intentar:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### Paso 2.5 — Conseguir tu clave de Gemini
1. Entra a **https://aistudio.google.com/apikey** (inicia sesión con Google).
2. Clic en **Create API key** y **copia** la clave.
3. En la carpeta del programa, **copia** el archivo `.env.example` y renómbralo a `.env`.
   ```powershell
   copy .env.example .env
   ```
4. Abre `.env` con el Bloc de notas y pega tu clave:
   ```
   GEMINI_API_KEY=pega_aqui_tu_clave
   ```
5. Guarda. **Nunca compartas este archivo** (contiene tu clave).

### Paso 2.6 — Probar que todo conecta
```powershell
python hola_mundo.py
```
Si dice **"Conexión con la Live API establecida"**, ¡todo quedó listo! ✅

---

## 3. Configurar el audio (lo más importante)

El truco es mandar **el sonido que quieres traducir** al cable (CABLE Input).
El programa lo captura de **CABLE Output**, lo traduce, y reproduce el resultado
en tus audífonos.

```
  Fuente (curso/reunión)  →  CABLE Input  →  [cable]  →  CABLE Output  →  el programa
                                                                              ↓ traduce
                                          oyes la traducción  ←  tus audífonos/bocinas
```

> 💡 Regla de oro: la **fuente** va a *CABLE Input*; tú **escuchas** por tus
> audífonos. La "Salida de audio" del programa **nunca** debe ser un cable.

### Cómo enrutar según lo que uses

**A) Un navegador (YouTube, Udemy, Coursera):**
1. Clic derecho en el ícono 🔊 (barra de tareas) → **Mezclador de volumen**.
2. Busca tu navegador (Chrome/Edge) → en **Dispositivo de salida** elige
   **CABLE Input (VB-Audio Virtual Cable)**.

**B) Zoom:**
1. En Zoom, flecha `^` junto al micrófono → **Seleccionar un altavoz**.
2. Elige **CABLE Input (VB-Audio Virtual Cable)**.

**C) Todo el sistema:**
1. Clic derecho en 🔊 → **Configuración de sonido**.
2. En **Salida**, elige **CABLE Input** como predeterminado.
   *(Recuerda regresarlo a tus audífonos al terminar.)*

---

## 4. Usar la aplicación

Con el entorno activado, abre la app:
```powershell
python app.py
```

Se abre la ventana. Configúrala así:

| Campo | Qué poner |
|---|---|
| **Idioma origen** | Déjalo en `Auto-detectar` (el modelo lo detecta solo). |
| **Idioma destino** | El idioma al que quieres traducir (ej. `Español`). |
| **Salida de audio** | Tus **audífonos** o **bocinas** (donde escuchas). |
| **Capturar de** | `CABLE Output (VB-Audio Virtual Cable)` (ya viene por defecto). |

Botones:
- **▶ Iniciar** — empieza a traducir. El estado pasa a *Traduciendo* (verde).
- **⏸ Pausar / Reanudar** — detiene/continúa la traducción (ahorra costo en pausa).
- **⏹ Detener** — termina la sesión.
- **🧹 Limpiar** — borra los subtítulos en pantalla.
- **☑ Mostrar inglés** — muestra también el texto del idioma original.

**Cambiar de idioma en vivo:** mientras está corriendo, solo cambia el menú
**Idioma destino** y en ~2 segundos se adapta solo, sin reiniciar.

Cuando pongas a sonar la fuente, en unos segundos verás los subtítulos avanzar y
oirás la traducción. `Ctrl+C` o **Detener** para parar.

---

## 5. Casos de uso

| Quiero traducir… | Pasos |
|---|---|
| **Un video de YouTube** | Rutea Chrome → CABLE Input (sección 3-A), destino = tu idioma, ▶ Iniciar. |
| **Un curso de Udemy/Coursera** | Igual que YouTube (es el navegador). |
| **Una reunión de Zoom** | Zoom → Speaker = CABLE Input (sección 3-B), ▶ Iniciar. |
| **Cualquier cosa del sistema** | Salida predeterminada = CABLE Input (sección 3-C). |

---

## 6. Problemas comunes y soluciones

| Síntoma | Causa probable | Solución |
|---|---|---|
| **Error `-9999`** al Iniciar | Dispositivo WASAPI/WDM-KS conflictivo (USB) | La app ya usa MME; elige otra **Salida de audio** (ej. Speakers). No uses dispositivos "WDM-KS". |
| **Error `-9985` (Device unavailable)** | Otra app (ej. Zoom) tiene tomado el dispositivo | Usa otra salida o cierra/redirige la otra app. |
| **La traducción se repite o se atora** | Hay un **eco** en el ruteo | Abre `Win+R` → `mmsys.cpl` → pestaña **Grabar** → `CABLE Output` → **Escuchar** → **desmarca** "Escuchar este dispositivo". |
| **No escucho la traducción** | La salida está en un cable o en un dispositivo que no usas | Pon **Salida de audio** = tus audífonos/bocinas reales. |
| **No aparecen subtítulos** | La fuente no está llegando al cable | Revisa que enrutaste el navegador/Zoom a **CABLE Input**. |
| **"Falta GEMINI_API_KEY"** | No creaste el `.env` o está vacío | Repite el Paso 2.5. |
| **Va con retraso de unos segundos** | Normal | Es la latencia del modelo en vivo; en clases grabadas no afecta. |

---

## 7. Preguntas frecuentes

**¿Es gratis?**
El programa sí. Gemini tiene un tier gratuito para probar; en plan de pago cuesta
~$0.037 USD por minuto de audio (~$2.2/hora). Pausar cuando no necesitas
traducir ahorra mucho.

**¿Oiré también el audio original?**
No: el original se va "por dentro" al cable y solo oyes la traducción (así no se
encima). Es lo ideal para no confundirte con dos voces.

**¿A qué idiomas traduce?**
A 70+ idiomas. El menú incluye español, inglés, francés, alemán, portugués,
italiano, japonés, coreano, chino, ruso, árabe e hindi.

**¿Detecta solo el idioma original?**
Sí, automáticamente. Por eso "Idioma origen" es solo informativo.

**¿Funciona en Mac o Linux?**
El código de Gemini sí, pero la captura de audio está pensada para Windows
(VB-CABLE). En Mac se usaría BlackHole y en Linux el monitor de PulseAudio.

**¿Es seguro VB-CABLE?**
Sí, es software conocido de VB-Audio. Descárgalo **solo** del sitio oficial
`vb-audio.com`.

---

¿Dudas o algo no funciona? Revisa la sección 6, o abre un *issue* en el
repositorio: https://github.com/joseIronMaker/traductor-audio-tiempo-real
