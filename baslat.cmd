@echo off
setlocal
chcp 65001 >nul
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  echo Python bulunamadi. Anaconda python PATH'te olmali.
  pause
  exit /b 1
)
%PY% "%~dp0dersmerkezi.py" %*
set "KOD=%ERRORLEVEL%"
if not "%KOD%"=="0" pause
exit /b %KOD%
