@echo off
title TF2 Chat Translator
cd /d "%~dp0"
where python >nul 2>nul || (echo Python isn't installed. Get it from https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^). & pause & exit /b)
:menu
echo.
echo  TF2 Chat Translator
echo  -------------------
echo  1. Russian to English         (overlay only, just you see it)
echo  2. All languages to English   (overlay only, just you see it)
echo  3. Russian to English         (said in chat for everyone)
echo  4. All languages to English   (said in chat for everyone)
echo  5. Setup (once: sets TF2's launch options, Steam must be closed)
echo.
set /p choice=Pick 1-5: 
if "%choice%"=="1" python translator.py --languages russian --output overlay
if "%choice%"=="2" python translator.py --languages all --output overlay
if "%choice%"=="3" python translator.py --languages russian --output chat
if "%choice%"=="4" python translator.py --languages all --output chat
if "%choice%"=="5" python setup_tf2.py
pause
goto menu
