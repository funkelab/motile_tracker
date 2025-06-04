#define AppName "MotileTracker"
#define AppVersion GetFileVersion('dist\MotileTracker\MotileTracker.exe')
#define AppURL "https://funkelab.github.io/motile_tracker"

[Setup]
AppName={#AppName}
AppVersion="1.0"
AppPublisherURL={#AppURL}
DefaultDirName={commonpf}\{#AppName}
LicenseFile="..\LICENSE"
OutputDir="..\dist\"
OutputBaseFilename={#AppName}Installer
Compression=lzma
SolidCompression=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\{#AppName}\{#AppName}.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\{#AppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppName}.exe"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppName}.exe"; Tasks: desktopicon
