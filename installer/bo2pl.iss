; Inno Setup script of the Polish subtitles/translation of Legacy of Kain: Blood Omen 2.
; The installer does not contain game data: it carries Bo2Patcher.exe, the patch manifest bo2pl.patch
; and our subtitle files. It finds the game, lets the patcher modify the user's own bo2.exe (and,
; later, the font in PreCode.big / Code.big) and copies the .cnv subtitle files into data\texts
; (see docs/patching.md).
;
; Build:  ISCC.exe /DAppVersion=1.0.0 /DPatcherExe=..\dist\Bo2Patcher.exe /DPatchFile=..\patch\bo2pl.patch bo2pl.iss

#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif
#ifndef PatcherExe
  #define PatcherExe "..\dist\Bo2Patcher.exe"
#endif
#ifndef PatchFile
  #define PatchFile "..\patch\bo2pl.patch"
#endif

[Setup]
AppId={{C1E7A4F2-6B1D-4F0B-9A55-7D7E0C5B21A9}
AppName=Legacy of Kain: Blood Omen 2 PL
AppVersion={#AppVersion}
AppPublisher=Grupa Polonizacyjna Nosgothica
AppPublisherURL=https://github.com/Grupa-Polonizacyjna-Nosgothica/blood-omen-2-pl
AppSupportURL=https://discord.gg/bJKCtJcaDg
; The installer works in the game's folder
DefaultDirName={code:GetDefaultGameDir}
AppendDefaultDirName=no
DirExistsWarning=no
UsePreviousAppDir=yes
DisableProgramGroupPage=yes
; Games in "Program Files" are not writable without administrator rights
PrivilegesRequired=admin
UninstallFilesDir={app}\Bo2PL
UninstallDisplayName=Legacy of Kain: Blood Omen 2 PL
CloseApplications=no
WizardStyle=modern
InfoBeforeFile=INSTALL.txt
OutputDir=..\dist
OutputBaseFilename=BO2-PL-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
; bo2.exe is a 32-bit game, but the installer itself does not depend on the bitness

[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Used by the wizard before anything is installed
Source: "{#PatcherExe}"; DestDir: "{tmp}"; Flags: dontcopy
Source: "{#PatchFile}"; DestDir: "{tmp}"; Flags: dontcopy
Source: "{#PatcherExe}"; DestDir: "{app}\Bo2PL"; Flags: ignoreversion
Source: "{#PatchFile}"; DestDir: "{app}\Bo2PL"; Flags: ignoreversion
Source: "reapply.cmd"; DestDir: "{app}\Bo2PL"; Flags: ignoreversion
; Subtitle files (record format: docs/captions.md); removed again by the uninstaller
Source: "..\subtitles\PL\*.cnv"; DestDir: "{app}\data\texts"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\Legacy of Kain Blood Omen 2 PL\{cm:ReapplyName}"; Filename: "{app}\Bo2PL\reapply.cmd"; WorkingDir: "{app}\Bo2PL"
Name: "{autoprograms}\Legacy of Kain Blood Omen 2 PL\{cm:UninstallName}"; Filename: "{uninstallexe}"

[CustomMessages]
polish.ReapplyName=Zastosuj spolszczenie ponownie
polish.UninstallName=Odinstaluj spolszczenie
polish.NotAGameDir=Ten folder nie wygląda na folder gry Legacy of Kain: Blood Omen 2 (brak plików bo2.exe i data\pc.rkv).%n%nWskaż główny folder gry (w GOG Galaxy: Zarządzaj instalacją, Pokaż folder).
polish.ErrVersion=Ta wersja gry nie jest obsługiwana.%n%nSprawdź integralność plików gry w kliencie Steam lub GOG i spróbuj ponownie.
polish.ErrRunning=Gra jest uruchomiona. Zamknij ją (oraz launcher) i spróbuj ponownie.
polish.ErrWrite=Nie można zapisać plików gry. Zamknij grę i launcher, upewnij się, że pliki nie są tylko do odczytu, i spróbuj ponownie.
polish.ErrSpace=Brak miejsca na dysku z grą.
polish.ErrChanged=Plik gry został zmieniony po poprzedniej instalacji (np. przez aktualizację lub sprawdzenie plików). Sprawdź integralność plików gry w kliencie Steam lub GOG i zainstaluj spolszczenie ponownie.
polish.ErrGeneric=Nie udało się zmodyfikować plików gry.
polish.ErrLog=Szczegóły zapisano w pliku:
polish.Patching=Modyfikowanie plików gry...
polish.PatchFailedHint=Spolszczenie nie zostało zastosowane. Po usunięciu problemu uruchom skrót "Zastosuj spolszczenie ponownie" z menu Start.
polish.Done=Spolszczenie zostało zainstalowane.
polish.UninstallRunning=Gra jest uruchomiona. Zamknij ją (oraz launcher) i uruchom dezinstalator ponownie.
polish.UninstallChanged=Plik gry został zmieniony po zainstalowaniu spolszczenia, więc nie można go automatycznie przywrócić. Sprawdź integralność plików gry w kliencie Steam lub GOG, aby przywrócić oryginał. Dezinstalacja będzie kontynuowana.
polish.UninstallFailed=Nie udało się przywrócić oryginalnych plików gry. Dezinstalacja została przerwana.
english.ReapplyName=Apply the translation again
english.UninstallName=Uninstall the translation
english.NotAGameDir=This folder does not look like the Legacy of Kain: Blood Omen 2 game folder (bo2.exe and data\pc.rkv are missing).%n%nSelect the main game folder (in GOG Galaxy: Manage installation, Show folder).
english.ErrVersion=This version of the game is not supported.%n%nVerify the game files in your Steam or GOG client and try again.
english.ErrRunning=The game is running. Close it (and its launcher) and try again.
english.ErrWrite=Cannot write the game files. Close the game and its launcher, make sure the files are not read-only, and try again.
english.ErrSpace=Not enough free disk space on the drive of the game.
english.ErrChanged=A game file was changed after the previous installation (for example by an update or a file verification). Verify the game files in your Steam or GOG client and install the translation again.
english.ErrGeneric=The game files could not be modified.
english.ErrLog=Details were saved to:
english.Patching=Modifying the game files...
english.PatchFailedHint=The translation was not applied. After fixing the problem run "Apply the translation again" from the Start menu.
english.Done=The translation is installed.
english.UninstallRunning=The game is running. Close it (and its launcher) and run the uninstaller again.
english.UninstallChanged=A game file was changed after the translation was installed, so it cannot be restored automatically. Verify the game files in your Steam or GOG client to get the original back. Uninstalling continues.
english.UninstallFailed=The original game files could not be restored. Uninstalling was cancelled.

[Code]
const
  GogGameId = '1207659101';       // Legacy of Kain: Blood Omen 2 on GOG (goggame-1207659101.info)
  SteamFolderName = 'Legacy of Kain Blood Omen 2';

var
  DetectedGameDir: String;
  DetectionDone: Boolean;

// ---------------------------------------------------------------- finding the game

function IsGameDir(const Dir: String): Boolean;
begin
  Result := (Dir <> '') and FileExists(AddBackslash(Dir) + 'bo2.exe')
            and FileExists(AddBackslash(Dir) + 'data\pc.rkv');
end;

// Value of a line like:  "key"   "value"  (Valve's text format); backslashes are doubled in the file
function VdfValue(const Line, Key: String): String;
var
  S: String;
  P: Integer;
begin
  Result := '';
  S := Trim(Line);
  if Pos('"' + Key + '"', S) <> 1 then Exit;
  S := Copy(S, Length(Key) + 3, MaxInt);
  P := Pos('"', S);
  if P = 0 then Exit;
  S := Copy(S, P + 1, MaxInt);
  P := Pos('"', S);
  if P = 0 then Exit;
  Result := Copy(S, 1, P - 1);
  StringChangeEx(Result, '\\', '\', True);
end;

function FindGogGame: String;
var
  GamePath: String;
begin
  Result := '';
  if RegQueryStringValue(HKLM32, 'SOFTWARE\GOG.com\Games\' + GogGameId, 'path', GamePath) and IsGameDir(GamePath) then
    Result := GamePath;
end;

// Best effort: the Steam app id is not known here, so look for the default folder name in every library
function FindSteamGame: String;
var
  SteamDir, Value, Candidate: String;
  Lines: TArrayOfString;
  I: Integer;
begin
  Result := '';
  if not RegQueryStringValue(HKLM32, 'SOFTWARE\Valve\Steam', 'InstallPath', SteamDir) then
    if not RegQueryStringValue(HKCU, 'Software\Valve\Steam', 'SteamPath', SteamDir) then Exit;
  StringChangeEx(SteamDir, '/', '\', True);

  Candidate := AddBackslash(SteamDir) + 'steamapps\common\' + SteamFolderName;
  if IsGameDir(Candidate) then
  begin
    Result := Candidate;
    Exit;
  end;
  // Other library folders are listed in libraryfolders.vdf
  if LoadStringsFromFile(AddBackslash(SteamDir) + 'steamapps\libraryfolders.vdf', Lines) then
    for I := 0 to GetArrayLength(Lines) - 1 do
    begin
      Value := VdfValue(Lines[I], 'path');
      if Value <> '' then
      begin
        Candidate := AddBackslash(Value) + 'steamapps\common\' + SteamFolderName;
        if IsGameDir(Candidate) then
        begin
          Result := Candidate;
          Exit;
        end;
      end;
    end;
end;

function GetDefaultGameDir(Param: String): String;
begin
  if not DetectionDone then
  begin
    DetectionDone := True;
    DetectedGameDir := FindGogGame;
    if DetectedGameDir = '' then DetectedGameDir := FindSteamGame;
  end;
  if DetectedGameDir <> '' then
    Result := DetectedGameDir
  else
    Result := ExpandConstant('{autopf32}') + '\GOG Galaxy\Games\Legacy of Kain Blood Omen 2';
end;

// ---------------------------------------------------------------- running the patcher

// Runs Bo2Patcher through cmd so that its messages end up in a log file. Returns the exit code, or -1.
function RunPatcher(const Exe, Arguments, LogFile: String): Integer;
var
  ResultCode: Integer;
begin
  if Exec(ExpandConstant('{cmd}'), '/C ""' + Exe + '" ' + Arguments + ' > "' + LogFile + '" 2>&1"', '',
          SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    Result := ResultCode
  else
    Result := -1;
end;

function MessageForExitCode(const Code: Integer): String;
begin
  case Code of
    3: Result := CustomMessage('ErrVersion');
    4: Result := CustomMessage('ErrRunning');
    5: Result := CustomMessage('ErrSpace');
    6: Result := CustomMessage('ErrChanged');
    7: Result := CustomMessage('ErrWrite');
  else
    Result := CustomMessage('ErrGeneric');
  end;
end;

// ---------------------------------------------------------------- wizard

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Dir, LogFile: String;
  Code: Integer;
begin
  Result := True;
  if CurPageID <> wpSelectDir then Exit;

  Dir := RemoveBackslash(WizardDirValue);
  if not IsGameDir(Dir) then
  begin
    MsgBox(CustomMessage('NotAGameDir'), mbError, MB_OK);
    Result := False;
    Exit;
  end;

  // Game build, running game and write access, before anything is copied
  ExtractTemporaryFile('Bo2Patcher.exe');
  ExtractTemporaryFile('bo2pl.patch');
  LogFile := ExpandConstant('{tmp}\check.log');
  Code := RunPatcher(ExpandConstant('{tmp}\Bo2Patcher.exe'),
                     'check "' + Dir + '" "' + ExpandConstant('{tmp}\bo2pl.patch') + '"', LogFile);
  if Code <> 0 then
  begin
    MsgBox(MessageForExitCode(Code), mbError, MB_OK);
    Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Dir, LogFile: String;
  Code: Integer;
begin
  if CurStep <> ssPostInstall then Exit;

  Dir := ExpandConstant('{app}');
  LogFile := Dir + '\Bo2PL\patch.log';
  WizardForm.StatusLabel.Caption := CustomMessage('Patching');
  Code := RunPatcher(Dir + '\Bo2PL\Bo2Patcher.exe',
                     'patch "' + Dir + '" "' + Dir + '\Bo2PL\bo2pl.patch"', LogFile);
  if Code <> 0 then
    MsgBox(MessageForExitCode(Code) + #13#10#13#10 + CustomMessage('ErrLog') + #13#10 + LogFile + #13#10#13#10
           + CustomMessage('PatchFailedHint'), mbError, MB_OK);
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
    WizardForm.FinishedLabel.Caption := CustomMessage('Done') + #13#10#13#10 + WizardForm.FinishedLabel.Caption;
end;

// ---------------------------------------------------------------- uninstall

function InitializeUninstall: Boolean;
var
  Dir: String;
  Code: Integer;
begin
  Result := True;
  Dir := ExpandConstant('{app}');
  if not FileExists(Dir + '\bo2.exe') then Exit; // the game is gone; nothing to restore

  Code := RunPatcher(Dir + '\Bo2PL\Bo2Patcher.exe',
                     'restore "' + Dir + '" "' + Dir + '\Bo2PL\bo2pl.patch"', Dir + '\Bo2PL\restore.log');
  case Code of
    0: Result := True;
    4: begin MsgBox(CustomMessage('UninstallRunning'), mbError, MB_OK); Result := False; end;
    6: MsgBox(CustomMessage('UninstallChanged'), mbInformation, MB_OK);
  else
    begin MsgBox(CustomMessage('UninstallFailed'), mbError, MB_OK); Result := False; end;
  end;
end;
