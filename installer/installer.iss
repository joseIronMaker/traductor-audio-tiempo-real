; Instalador del Traductor de Audio en Vivo (Inno Setup)
; Compilar con: ISCC.exe installer.iss

#define MyAppName "Traductor de Audio en Vivo"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "joseIronMaker"
#define MyAppExeName "TraductorAudio.exe"
#define MyAppURL "https://github.com/joseIronMaker/traductor-audio-tiempo-real"

[Setup]
AppId={{8F3A1C2E-5B6D-4E7F-9A0B-1C2D3E4F5A6B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\TraductorAudioGemini
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=TraductorAudio-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayName={#MyAppName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\TraductorAudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\manual\manual_usuario.pdf"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Manual de usuario"; Filename: "{app}\manual_usuario.pdf"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "https://vb-audio.com/Cable"; Description: "Descargar VB-CABLE (necesario para capturar el audio del sistema)"; Flags: shellexec postinstall skipifsilent unchecked
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir el traductor ahora"; Flags: nowait postinstall skipifsilent

[Messages]
spanish.WelcomeLabel2=Este asistente instalará [name] en tu equipo.%n%nIMPORTANTE: el programa necesita VB-CABLE (gratis) para capturar el audio, y una clave gratuita de Gemini. El manual incluido explica cómo configurar ambos.
spanish.FinishedLabel=La instalación terminó. Recuerda: si aún no lo tienes, instala VB-CABLE (marca la casilla de abajo) y al abrir el programa pega tu clave de Gemini.
