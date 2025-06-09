[Setup]
AppName=Pygame
AppVersion=1.0
DefaultDirName={pf}\Pygame
DefaultGroupName=Pygame
OutputDir=dist
OutputBaseFilename=setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\\assets\\*"; DestDir: "{app}\\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "在桌面创建快捷方式"; GroupDescription: "附加任务:"

[Icons]
Name: "{group}\Pygame"; Filename: "{app}\main.exe"
Name: "{group}\卸载 Pygame"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Pygame"; Filename: "{app}\main.exe"; Tasks: desktopicon