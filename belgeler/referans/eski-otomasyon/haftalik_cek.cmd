@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0otomasyon\haftalik_cek.ps1" %*
set KOD=%ERRORLEVEL%
echo.
echo Cikis kodu: %KOD%
pause
exit /b %KOD%
