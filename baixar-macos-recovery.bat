@echo off
REM =============================================================================
REM Script: Baixar macOS Recovery para Hackintosh
REM Uso: Execute este script DEPOIS de rodar preparar-efi-hackintosh.ps1
REM =============================================================================

echo =============================================
echo  Baixar macOS Recovery - ASUS Vivobook 4800HS
echo =============================================
echo.
echo Selecione a versao do macOS:
echo.
echo  [1] macOS Ventura (13) - Estavel
echo  [2] macOS Sonoma (14) - RECOMENDADO
echo  [3] macOS Sequoia (15) - Mais recente
echo.

set /p CHOICE="Escolha (1/2/3): "

cd /d "%~dp0\HackintoshEFI\macrecovery"

if "%CHOICE%"=="1" (
    echo Baixando macOS Ventura...
    py macrecovery.py -b Mac-4B682C642B45593E -m 00000000000000000 download
)
if "%CHOICE%"=="2" (
    echo Baixando macOS Sonoma...
    py macrecovery.py -b Mac-226CB3C6A851A671 -m 00000000000000000 download
)
if "%CHOICE%"=="3" (
    echo Baixando macOS Sequoia...
    py macrecovery.py -b Mac-937A206F2EE63C01 -m 00000000000000000 download
)

echo.
echo Movendo arquivos para com.apple.recovery.boot...

move /Y "%~dp0\HackintoshEFI\macrecovery\BaseSystem*" "%~dp0\HackintoshEFI\com.apple.recovery.boot\" 2>nul
move /Y "%~dp0\HackintoshEFI\macrecovery\RecoveryImage*" "%~dp0\HackintoshEFI\com.apple.recovery.boot\" 2>nul

echo.
echo =============================================
echo  Download concluido!
echo  Arquivos em: %~dp0\HackintoshEFI\com.apple.recovery.boot\
echo.
echo  PROXIMO PASSO:
echo  Copie as pastas EFI e com.apple.recovery.boot
echo  para a raiz do seu pendrive formatado em FAT32
echo =============================================

pause
