#define MyAppName "HighEnna"
#define MyAppVersion "2.0.0"
#define MyAppExeName "HighEnna.exe"
#define MyAppPublisher "Landis+Gyr, Inc."
#define MyAppAuthor "Mateus Felipe Crevelin"

[Setup]
AppId={{6236D968-C4F0-4EAC-A024-C82D34CC3219}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName}_{#MyAppVersion}
AppPublisher={#MyAppPublisher}

PrivilegesRequired=admin

DefaultDirName={pf}\{#MyAppName}
UsePreviousAppDir=no

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes

OutputDir=..\output
OutputBaseFilename={#MyAppName}_{#MyAppVersion}_windows_setup
SetupIconFile=.\assets\Windows setup.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\HighEnna-Graphical\build\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\HighEnna-Graphical\build\dist\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCR; Subkey: ".heproj"; ValueType: string; ValueData: "HighEnnaProject"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "HighEnnaProject"; ValueType: string; ValueData: "HighEnna Project"; Flags: uninsdeletekey
Root: HKCR; Subkey: "HighEnnaProject\DefaultIcon"; ValueType: string; ValueData: "{app}\HighEnna.exe,0"
Root: HKCR; Subkey: "HighEnnaProject\shell\open\command"; ValueType: string; ValueData: """{app}\HighEnna.exe"" ""%1"""