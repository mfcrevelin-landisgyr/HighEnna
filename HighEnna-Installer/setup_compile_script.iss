#define MyAppName "HighEnna"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Landis+Gyr, Inc."
#define MyAppExeName "HighEnna.exe"

[Setup]
AppId={{6236D968-C4F0-4EAC-A024-C82D34CC3219}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName}_{#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE.txt
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputBaseFilename={#MyAppName}_{#MyAppVersion}_windows_setup
SetupIconFile=.\Windows setup.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\HighEnna-Graphical\build\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\HighEnna-Graphical\build\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

