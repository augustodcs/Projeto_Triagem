@echo off
chcp 65001 >nul 2>&1
title Terra Fertil Jardins - Sistema de Triagem
echo ============================================================
echo   TERRA FERTIL JARDINS - SISTEMA DE TRIAGEM DE PRESTADORES
echo ============================================================
echo.

REM === 1. Tenta o executavel compilado (versao sem Python) ===
if exist "dist\TerraFertil_Triagem\TerraFertil_Triagem.exe" (
    echo Iniciando versao compilada...
    start "" "dist\TerraFertil_Triagem\TerraFertil_Triagem.exe"
    exit /b 0
)

if exist "TerraFertil_Triagem.exe" (
    echo Iniciando versao compilada...
    start "" "TerraFertil_Triagem.exe"
    exit /b 0
)

REM === 2. Tenta o ambiente virtual local (.venv) ===
if exist ".venv\Scripts\python.exe" (
    echo Iniciando pelo ambiente virtual local...
    echo.
    ".venv\Scripts\python.exe" app.py
    pause
    exit /b
)

REM === 3. Verifica se o Python esta instalado ===
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Iniciando o sistema...
    echo.
    py app.py
    pause
    exit /b
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Iniciando o sistema...
    echo.
    python app.py
    pause
    exit /b
)

REM === 4. Python nao encontrado: oferecer instalacao automatica ===
echo.
echo ============================================================
echo  ATENCAO: Python nao encontrado no computador!
echo ============================================================
echo.
echo O Python e necessario para rodar este sistema.
echo Deseja baixar e instalar agora automaticamente?
echo.
echo   [S] Sim, instalar Python automaticamente
echo   [N] Nao, eu instalarei manualmente
echo.
set /p opcao="Digite S ou N e pressione Enter: "

if /i "%opcao%"=="S" goto instalar_python
if /i "%opcao%"=="N" goto instrucoes_manuais
goto instrucoes_manuais

:instalar_python
echo.
echo Baixando Python 3.12 (pode demorar alguns minutos)...
echo Nao feche esta janela!
echo.

REM Tenta baixar com PowerShell
powershell -Command "& {
    $url = 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe'
    $dest = '%TEMP%\python_installer.exe'
    Write-Host 'Baixando...'
    try {
        (New-Object Net.WebClient).DownloadFile($url, $dest)
        Write-Host 'Download concluido!'
    } catch {
        Write-Host 'Erro no download: ' + $_.Exception.Message
        exit 1
    }
}"

if not exist "%TEMP%\python_installer.exe" (
    echo.
    echo Nao foi possivel baixar automaticamente.
    goto instrucoes_manuais
)

echo.
echo Instalando Python (aguarde, o instalador vai abrir)...
echo.
echo IMPORTANTE: Na tela de instalacao, marque a opcao:
echo   [ ] Add python.exe to PATH  <<< MARQUE ESTA CAIXINHA!
echo.
pause

"%TEMP%\python_installer.exe" /passive PrependPath=1 Include_test=0

echo.
echo Instalacao concluida! Reinicie o arquivo Iniciar_Triagem.bat
echo para iniciar o sistema.
echo.
pause
exit /b

:instrucoes_manuais
echo.
echo ============================================================
echo  Como instalar o Python manualmente:
echo ============================================================
echo.
echo  1. Acesse: https://www.python.org/downloads/
echo  2. Clique no botao amarelo "Download Python"
echo  3. Abra o arquivo baixado
echo  4. MARQUE A OPCAO "Add python.exe to PATH" (embaixo)
echo  5. Clique em "Install Now"
echo  6. Apos instalar, execute este arquivo novamente
echo.
echo ============================================================
echo.
start "" "https://www.python.org/downloads/"
pause
