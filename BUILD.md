# Cómo compilar el ejecutable y el instalador

El programa se distribuye como un **instalador `.exe`** que ya trae Python y todas
las librerías adentro (el usuario final no instala nada de Python).

## Requisitos para compilar
- Windows con el proyecto ya configurado (ver [MANUAL.md](MANUAL.md), pasos 2.1–2.4).
- [PyInstaller](https://pyinstaller.org): `pip install pyinstaller`
- [Inno Setup 6](https://jrsoftware.org/isdl.php) (para el instalador).

## 1. Generar el ejecutable (PyInstaller)
Desde la carpeta del proyecto, con el entorno virtual activado:

```powershell
pyinstaller --noconfirm --windowed --name TraductorAudio `
  --collect-all soundfile --collect-all sounddevice `
  --collect-all google --collect-all certifi `
  app.py
```

Resultado: `dist\TraductorAudio\` (carpeta con `TraductorAudio.exe` + librerías).
Puedes probarlo ejecutando `dist\TraductorAudio\TraductorAudio.exe`.

## 2. Generar el instalador (Inno Setup)
```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\installer.iss
```

Resultado: `installer\Output\TraductorAudio-Setup.exe`.

## Notas
- El instalador incluye el manual (`manual/manual_usuario.pdf`) y crea accesos
  directos en el menú Inicio y el escritorio.
- **VB-CABLE no se incluye** (es un driver de terceros con su propia licencia);
  el instalador ofrece abrir su página de descarga al terminar.
- La **clave de Gemini** no se empaqueta: el programa la pide en una ventana la
  primera vez y la guarda en `%APPDATA%\TraductorAudioGemini`.
- Las carpetas `build/`, `dist/` y `installer/Output/` están en `.gitignore`
  (no se suben al repo). Distribuye el `Setup.exe` vía *GitHub Releases*.
