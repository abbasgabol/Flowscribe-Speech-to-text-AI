#define AppVersion "0.4.0"
[Setup]
AppId={{58F59443-B96A-4609-A794-8815C283B749}
AppName=Local Dictation
AppVersion={#AppVersion}
AppPublisher=Abbas Gabol
DefaultDirName={localappdata}\Programs\Local Dictation
DefaultGroupName=Local Dictation
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
InfoBeforeFile=INSTALL-NOTES.txt
WizardStyle=modern
WizardImageFile=wizard.bmp
WizardSmallImageFile=wizard-small.bmp
WizardImageStretch=yes
WizardSizePercent=110
SetupIconFile=..\assets\app.ico
UninstallDisplayIcon={app}\LocalDictation.exe
OutputDir=..\website\dist\downloads
OutputBaseFilename=LocalDictation-Setup
Compression=lzma2/fast
SolidCompression=yes
LZMANumBlockThreads=2
CloseApplications=yes
RestartApplications=no
UninstallDisplayName=Local Dictation

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce

[Files]
Source: "..\dist\LocalDictation\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\models\base.en\config.json"; DestDir: "{app}\models\base.en"; Flags: ignoreversion
Source: "..\models\base.en\model.bin"; DestDir: "{app}\models\base.en"; Flags: ignoreversion
Source: "..\models\base.en\tokenizer.json"; DestDir: "{app}\models\base.en"; Flags: ignoreversion
Source: "..\models\base.en\vocabulary.txt"; DestDir: "{app}\models\base.en"; Flags: ignoreversion
Source: "..\models\punctuation\model.int8.onnx"; DestDir: "{app}\models\punctuation"; Flags: ignoreversion
Source: "..\models\punctuation\bpe.vocab"; DestDir: "{app}\models\punctuation"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\THIRD-PARTY-NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "INSTALL-NOTES.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Local Dictation"; Filename: "{app}\LocalDictation.exe"
Name: "{autodesktop}\Local Dictation"; Filename: "{app}\LocalDictation.exe"; Tasks: desktopicon

[InstallDelete]
; Refresh only this app's managed runtime on upgrades. User preferences and
; model files are stored elsewhere and are not part of this cleanup.
Type: filesandordirs; Name: "{app}\_internal"; Check: HasPreviousRuntime

[Run]
Filename: "{app}\LocalDictation.exe"; Description: "Launch Local Dictation"; Flags: nowait postinstall skipifsilent

[Code]
function HasPreviousRuntime: Boolean;
begin
  Result := FileExists(ExpandConstant('{app}\LocalDictation.exe')) and
    FileExists(ExpandConstant('{app}\unins000.exe'));
end;
