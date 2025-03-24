#define AppName MotileTracker
#define AppVersion GetFileVersion('dist\MotileTracker\MotileTracker.exe')

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={pf}\{#AppName}
OutputDir=dist
OutputBaseFilename={#AppName}Installer
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\{#AppName}\{#AppName}.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppName}.exe"
