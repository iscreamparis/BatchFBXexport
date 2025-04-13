@echo off
setlocal EnableDelayedExpansion

echo FBX Animation Preview Tool
echo =========================

if "%1"=="" (
  echo ERROR: No folder provided. Please drag a folder onto this batch file.
  pause
  exit /b 1
)

set FOLDER=%~f1
echo Processing folder: %FOLDER%

REM Check if the folder exists
if not exist "%FOLDER%" (
  echo ERROR: Folder not found: %FOLDER%
  pause
  exit /b 1
)

REM Create export folder
if not exist "%FOLDER%\exported_fbx" mkdir "%FOLDER%\exported_fbx"

REM Find all CASC files in the folder
set CASC_COUNT=0
for %%F in ("%FOLDER%\*.casc") do (
  set /a CASC_COUNT+=1
)

if %CASC_COUNT% EQU 0 (
  echo ERROR: No .casc files found in folder: %FOLDER%
  pause
  exit /b 1
)

echo Found %CASC_COUNT% CASC files to process.

REM Define paths
set CASC_SCRIPT=G:\Mon Drive\scripts\fbxAnimationPreview\BatchExportFBXsegments.py
set EXPORT_SCRIPT=G:\Mon Drive\scripts\fbxAnimationPreview\export_all_segments.py
set COMMANDS_DIR=C:\Program Files\Cascadeur\resources\scripts\python\commands
set CASCADEUR="C:\Program Files\Cascadeur\cascadeur.exe"
set BLENDER="C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"

REM Check if necessary files and applications exist
if not exist "%CASC_SCRIPT%" (
  echo ERROR: Script not found: %CASC_SCRIPT%
  pause
  exit /b 1
)

if not exist "%EXPORT_SCRIPT%" (
  echo ERROR: Script not found: %EXPORT_SCRIPT%
  pause
  exit /b 1
)

if not exist %CASCADEUR% (
  echo ERROR: Cascadeur executable not found: %CASCADEUR%
  echo Please update the path in this batch file.
  pause
  exit /b 1
)

if not exist %BLENDER% (
  echo ERROR: Blender executable not found: %BLENDER%
  echo Please update the path in this batch file.
  pause
  exit /b 1
)

REM Copy script to Cascadeur commands directory
echo Copying script to Cascadeur directory...
if not exist "%COMMANDS_DIR%" (
  echo ERROR: Cascadeur scripts directory not found: %COMMANDS_DIR%
  pause
  exit /b 1
)

copy /Y "%CASC_SCRIPT%" "%COMMANDS_DIR%\" > nul

REM Process each CASC file
for %%F in ("%FOLDER%\*.casc") do (
  set CASC_FILE=%%F
  echo Processing CASC file: !CASC_FILE!
  
  REM Find TXT file with same name
  set TXT_FILE=!CASC_FILE:.casc=.txt!
  if not exist "!TXT_FILE!" (
    echo WARNING: No matching .txt file found for !CASC_FILE! - skipping
    continue
  )

  echo Found TXT file: !TXT_FILE!

  REM Create a config file with ABSOLUTE paths for this CASC file
  echo Writing config file with absolute paths...
  echo !CASC_FILE! > "G:\Mon Drive\scripts\fbxAnimationPreview\export_config.txt"
  echo %FOLDER%\exported_fbx >> "G:\Mon Drive\scripts\fbxAnimationPreview\export_config.txt"

  REM Clear log files for this run
  echo. > "G:\Mon Drive\scripts\fbxAnimationPreview\export_log.txt"
  echo. > "G:\Mon Drive\scripts\fbxAnimationPreview\orchestrator_log.txt"

  REM Run orchestration script to export segments for this file
  echo Running export_all_segments.py for !CASC_FILE!...
  python "%EXPORT_SCRIPT%" %CASCADEUR%
  if !ERRORLEVEL! NEQ 0 (
    echo ERROR: FBX export failed for !CASC_FILE! with error code !ERRORLEVEL!
    type "G:\Mon Drive\scripts\fbxAnimationPreview\orchestrator_log.txt"
    echo Continuing with next file...
  )
)

REM Check for exported FBX files
echo Checking for exported FBX files...
dir /b "%FOLDER%\exported_fbx\*.fbx" 2>nul
if %ERRORLEVEL% NEQ 0 (
  echo ERROR: No FBX files were exported.
  type "G:\Mon Drive\scripts\fbxAnimationPreview\orchestrator_log.txt"
  pause
  exit /b 1
)

REM Run Blender to render each FBX file individually
echo Running Blender to render FBX files...
for %%F in ("%FOLDER%\exported_fbx\*.fbx") do (
  echo Processing FBX file in Blender: %%F
  %BLENDER% --background --python "G:\Mon Drive\scripts\fbxAnimationPreview\blender_render_single.py" -- "%%F"
  if !ERRORLEVEL! NEQ 0 (
    echo WARNING: Blender rendering failed for %%F with error code !ERRORLEVEL!
  )
)

echo All done!
pause