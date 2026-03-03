# =============================================================================
# Script: Copiar EFI e Recovery para o Pendrive
# Uso: .\copiar-para-pendrive.ps1 -DriveLetter "E"
# =============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$DriveLetter,
    [string]$SourceDir = "$PSScriptRoot\HackintoshEFI"
)

$ErrorActionPreference = "Stop"

$drive = "${DriveLetter}:"

if (-not (Test-Path $drive)) {
    Write-Error "Drive $drive nao encontrado! Conecte o pendrive e tente novamente."
    exit 1
}

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Copiar EFI para Pendrive ($drive)" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Verificar arquivos de origem
$efiSource = Join-Path $SourceDir "EFI"
$recoverySource = Join-Path $SourceDir "com.apple.recovery.boot"

if (-not (Test-Path $efiSource)) {
    Write-Error "Pasta EFI nao encontrada em: $efiSource"
    Write-Error "Execute preparar-efi-hackintosh.ps1 primeiro!"
    exit 1
}

# Verificar se recovery existe
$hasRecovery = Test-Path $recoverySource
if (-not $hasRecovery) {
    Write-Warning "Pasta com.apple.recovery.boot nao encontrada!"
    Write-Warning "Execute baixar-macos-recovery.bat primeiro!"
}

# Copiar EFI
Write-Host "`nCopiando pasta EFI..." -ForegroundColor Yellow
$efiDest = Join-Path $drive "EFI"
if (Test-Path $efiDest) {
    Write-Host "  Removendo EFI existente no pendrive..." -ForegroundColor Gray
    Remove-Item $efiDest -Recurse -Force
}
Copy-Item $efiSource -Destination $efiDest -Recurse -Force
Write-Host "  EFI copiada com sucesso!" -ForegroundColor Green

# Copiar Recovery
if ($hasRecovery) {
    Write-Host "`nCopiando pasta com.apple.recovery.boot..." -ForegroundColor Yellow
    $recoveryDest = Join-Path $drive "com.apple.recovery.boot"
    if (Test-Path $recoveryDest) {
        Remove-Item $recoveryDest -Recurse -Force
    }
    Copy-Item $recoverySource -Destination $recoveryDest -Recurse -Force
    Write-Host "  Recovery copiada com sucesso!" -ForegroundColor Green
}

# Listar conteúdo final
Write-Host "`n--- Conteudo do pendrive ---" -ForegroundColor Cyan
Get-ChildItem $drive -Recurse -Depth 2 | Select-Object FullName | Format-Table -AutoSize

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host " Pendrive pronto! Pode bootar por ele." -ForegroundColor Green
Write-Host " Lembre-se de configurar a BIOS antes." -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Cyan
