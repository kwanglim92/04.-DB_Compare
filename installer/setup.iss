; ============================================
; DB_Compare QC Tool - Inno Setup Script
; Version: 2.0.0
; ============================================

#define MyAppName "DB Compare QC Tool"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Park Systems"
#define MyAppExeName "DB_Compare_QC_Tool.exe"
#define MyAppURL "https://www.parksystems.com"

[Setup]
; Unique application identifier
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation paths
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output settings
OutputDir=output
OutputBaseFilename=DB_Compare_QC_Tool_Setup_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

; Require admin rights (for Program Files)
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Icon (optional)
; SetupIconFile=..\assets\icon.ico
; UninstallDisplayIcon={app}\{#MyAppExeName}

; Allow user to choose installation directory
AllowNoIcons=yes
DisableDirPage=no

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable
Source: "..\dist\DB_Compare_QC_Tool.exe"; DestDir: "{app}"; Flags: ignoreversion

; Config files - only copy if they don't already exist (preserve user config on upgrade)
Source: "..\dist\config\common_base.json"; DestDir: "{app}\config"; Flags: onlyifdoesntexist
Source: "..\dist\config\profiles\*"; DestDir: "{app}\config\profiles"; Flags: onlyifdoesntexist recursesubdirs createallsubdirs
Source: "..\dist\config\settings.json"; DestDir: "{app}\config"; Flags: onlyifdoesntexist

; Create empty directories
[Dirs]
Name: "{app}\config"
Name: "{app}\config\profiles"
Name: "{app}\config\backup"
Name: "{app}\logs"
Name: "{app}\reports"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Launch after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Backup existing config before upgrade
procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigPath, BackupPath: string;
  BackupDir: string;
begin
  if CurStep = ssInstall then
  begin
    // Check if we're upgrading (config exists)
    ConfigPath := ExpandConstant('{app}\config\common_base.json');
    if FileExists(ConfigPath) then
    begin
      // Create backup of existing config
      BackupDir := ExpandConstant('{app}\config\backup');
      ForceDirectories(BackupDir);
      BackupPath := BackupDir + '\common_base_pre_upgrade.json';
      FileCopy(ConfigPath, BackupPath, False);
      
      // Also backup profiles
      // (Profiles are preserved due to onlyifdoesntexist flag)
    end;
  end;
end;

// Show message after installation
procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
  begin
    // Optional: Show tips
  end;
end;
