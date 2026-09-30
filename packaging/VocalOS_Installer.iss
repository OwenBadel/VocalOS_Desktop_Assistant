[Setup]
; Información General
AppName=VocalOS Desktop Assistant
AppVersion=1.0.0
AppPublisher=Owen Badel Hooker
AppPublisherURL=https://github.com/OwenBadel/VocalOS_Desktop_Assistant

; Directorio de Instalación en Program Files o LocalAppData
DefaultDirName={autopf}\VocalOS
DisableProgramGroupPage=yes

; Iconos e Interfaz
UninstallDisplayIcon={app}\VocalOS.exe

; Archivo de Salida (Instalador final compilado)
OutputDir=..\dist
OutputBaseFilename=VocalOS_Instalador_v1.0

; Compresión Ultra LZMA2
Compression=lzma2/ultra64
SolidCompression=yes

; Arquitectura de 64 bits
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Iniciar VocalOS automáticamente en segundo plano al encender Windows"; GroupDescription: "Arranque del Sistema:"

[Files]
; Toma la distribución compilada por PyInstaller y la empaqueta
Source: "..\dist\VocalOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\VocalOS Desktop Assistant"; Filename: "{app}\VocalOS.exe"
Name: "{autodesktop}\VocalOS"; Filename: "{app}\VocalOS.exe"; Tasks: desktopicon
; Acceso directo de arranque silencioso en la carpeta de inicio de Windows
Name: "{userstartup}\VocalOS"; Filename: "{app}\VocalOS.exe"; Parameters: "--tray"; Tasks: startup

[Run]
Filename: "{app}\VocalOS.exe"; Parameters: "--tray"; Description: "Iniciar VocalOS en segundo plano ahora"; Flags: nowait postinstall skipifsilent
