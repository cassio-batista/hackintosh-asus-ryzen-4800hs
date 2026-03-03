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
echo  [2] macOS Sonoma (14) - Estavel (testado neste projeto)
echo  [3] macOS Sequoia (15) - Recente
echo  [4] macOS Tahoe (16) - Mais recente (requer kexts atualizados!)
echo.

set /p CHOICE="Escolha (1/2/3/4): "

cd /d "%~dp0\HackintoshEFI\macrecovery"

if "%CHOICE%"=="1" (
    echo Baixando macOS Ventura...
    py macrecovery.py -b Mac-B4831CEBD52A0C4C -m 00000000000000000 download
)
if "%CHOICE%"=="2" (
    echo Baixando macOS Sonoma...
    py macrecovery.py -b Mac-827FAC58A8FDFA22 -m 00000000000000000 download
)
if "%CHOICE%"=="3" (
    echo Baixando macOS Sequoia...
    py macrecovery.py -b Mac-7BA5B2D9E42DDD94 -m 00000000000000000 download
)
if "%CHOICE%"=="4" (
    echo Baixando macOS Tahoe...
    echo AVISO: Verifique se NootedRed e itlwm suportam Tahoe antes de instalar!
    py macrecovery.py -b Mac-CFF7D910A743CAAF -m 00000000000000000 -os latest download
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
