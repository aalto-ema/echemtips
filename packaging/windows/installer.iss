; Per-user Windows x64 installer; no drivers, services or user-data deletion.
#ifndef AppVersion
  #error AppVersion is required
#endif
#ifndef BundleDir
  #error BundleDir is required
#endif
#ifndef ArtifactDir
  #error ArtifactDir is required
#endif
[Setup]
AppId={{95FE1A94-9D9F-4D79-9B3B-15AEC5B02AF0}
AppName=eChemTips
AppVersion={#AppVersion}
AppPublisher=Aalto EMA / eChemTips contributors
AppPublisherURL=https://github.com/aalto-ema/echemtips
AppSupportURL=https://github.com/aalto-ema/echemtips/issues
AppUpdatesURL=https://github.com/aalto-ema/echemtips/releases
DefaultDirName={localappdata}\Programs\eChemTips
DefaultGroupName=eChemTips
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.22000
OutputDir={#ArtifactDir}
OutputBaseFilename=eChemTips-{#AppVersion}-windows-x64-setup
SetupIconFile=..\..\echemtips\assets\echemtips.ico
UninstallDisplayIcon={app}\eChemTips.exe
LicenseFile=..\..\LICENSE
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
CloseApplications=no
RestartApplications=no
AppMutex=Local\eChemTipsDesktop
ChangesAssociations=yes
#ifdef SignedBuild
SignTool=release
SignedUninstaller=yes
#endif

[Tasks]
Name: desktopicon; Description: "Create desktop shortcuts"; GroupDescription: "Shortcuts:"; Flags: unchecked
Name: recordings; Description: "Add eChemTips Analysis to Open with for CSV recordings (does not change the default app)"; GroupDescription: "Recording integration:"; Flags: unchecked

[Dirs]
Name: "{userdocs}\eChemTips"; Flags: uninsneveruninstall

[Files]
Source: "{#BundleDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\eChemTips Control"; Filename: "{app}\eChemTips.exe"; WorkingDir: "{userdocs}\eChemTips"
Name: "{group}\eChemTips Analysis"; Filename: "{app}\eChemTips.exe"; Parameters: "--analysis"; WorkingDir: "{userdocs}\eChemTips"
Name: "{group}\Documentation"; Filename: "https://aalto-ema.github.io/echemtips/"
Name: "{autodesktop}\eChemTips Control"; Filename: "{app}\eChemTips.exe"; WorkingDir: "{userdocs}\eChemTips"; Tasks: desktopicon
Name: "{autodesktop}\eChemTips Analysis"; Filename: "{app}\eChemTips.exe"; Parameters: "--analysis"; WorkingDir: "{userdocs}\eChemTips"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Classes\eChemTips.Recording"; ValueType: string; ValueName: ""; ValueData: "eChemTips recording"; Flags: uninsdeletekey; Tasks: recordings
Root: HKCU; Subkey: "Software\Classes\eChemTips.Recording\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\eChemTips.exe,0"; Tasks: recordings
Root: HKCU; Subkey: "Software\Classes\eChemTips.Recording\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\eChemTips.exe"" --analysis ""%1"""; Tasks: recordings
Root: HKCU; Subkey: "Software\Classes\.csv\OpenWithProgids"; ValueType: string; ValueName: "eChemTips.Recording"; ValueData: ""; Flags: uninsdeletevalue; Tasks: recordings

; Deliberately no UninstallDelete: settings, calibrations and recordings survive.
