[Setup]
AppName=save
AppVersion=1.0
DefaultDirName={pf}\save
DefaultGroupName=save
OutputDir=dist
OutputBaseFilename=setup
Compression=lzma
SolidCompression=yes
SetupIconFile=dist\save.ico

[Files]
Source: "dist\\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\\assets\\*"; DestDir: "{app}\\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\\save.ico"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "在桌面创建快捷方式"; GroupDescription: "附加任务:"

[Icons]
Name: "{group}\save"; Filename: "{app}\main.exe"; IconFilename: "{app}\save.ico"
Name: "{group}\卸载 save"; Filename: "{uninstallexe}"
Name: "{commondesktop}\save"; Filename: "{app}\main.exe"; Tasks: desktopicon; IconFilename: "{app}\save.ico"