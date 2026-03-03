# =============================================================================
# Checklist de Verificação - Hackintosh ASUS Vivobook 4800HS
# Execute para verificar se sua EFI está completa antes de bootar
# =============================================================================

param(
    [string]$EfiDir = "$PSScriptRoot\HackintoshEFI\EFI"
)

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Verificação da EFI - Hackintosh Ryzen 4800HS" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0
$warnings = 0

function Check-File {
    param([string]$Path, [string]$Label, [bool]$Required = $true)
    $fullPath = Join-Path $EfiDir $Path
    if (Test-Path $fullPath) {
        Write-Host "  [OK] $Label" -ForegroundColor Green
        return $true
    }
    else {
        if ($Required) {
            Write-Host "  [ERRO] $Label — FALTANDO!" -ForegroundColor Red
            $script:errors++
        }
        else {
            Write-Host "  [AVISO] $Label — Não encontrado (opcional)" -ForegroundColor Yellow
            $script:warnings++
        }
        return $false
    }
}

# --- Boot ---
Write-Host "BOOT:" -ForegroundColor White
Check-File "BOOT\BOOTx64.efi" "BOOTx64.efi"

# --- Drivers ---
Write-Host "`nDRIVERS:" -ForegroundColor White
Check-File "OC\Drivers\HfsPlus.efi" "HfsPlus.efi"
Check-File "OC\Drivers\OpenRuntime.efi" "OpenRuntime.efi"
Check-File "OC\Drivers\ResetNvramEntry.efi" "ResetNvramEntry.efi" $false

# --- SSDTs ---
Write-Host "`nACPI (SSDTs):" -ForegroundColor White
Check-File "OC\ACPI\SSDT-EC-USBX.aml" "SSDT-EC-USBX.aml"
Check-File "OC\ACPI\SSDT-PNLF.aml" "SSDT-PNLF.aml"
Check-File "OC\ACPI\SSDT-ALS0.aml" "SSDT-ALS0.aml" $false

# --- Kexts Obrigatórios ---
Write-Host "`nKEXTS OBRIGATÓRIOS:" -ForegroundColor White
Check-File "OC\Kexts\Lilu.kext" "Lilu.kext"
Check-File "OC\Kexts\VirtualSMC.kext" "VirtualSMC.kext"
Check-File "OC\Kexts\NootedRed.kext" "NootedRed.kext (iGPU AMD Vega)"

# --- Kexts Importantes ---
Write-Host "`nKEXTS IMPORTANTES:" -ForegroundColor White
Check-File "OC\Kexts\AppleALC.kext" "AppleALC.kext (Áudio)"
Check-File "OC\Kexts\AppleMCEReporterDisabler.kext" "AppleMCEReporterDisabler.kext"
Check-File "OC\Kexts\NVMeFix.kext" "NVMeFix.kext"
Check-File "OC\Kexts\VoodooPS2Controller.kext" "VoodooPS2Controller.kext (Teclado)"
Check-File "OC\Kexts\ForgedInvariant.kext" "ForgedInvariant.kext (TSC Sync)"
Check-File "OC\Kexts\RestrictEvents.kext" "RestrictEvents.kext"

# --- Kexts Laptop ---
Write-Host "`nKEXTS LAPTOP:" -ForegroundColor White
Check-File "OC\Kexts\SMCBatteryManager.kext" "SMCBatteryManager.kext (Bateria)"
Check-File "OC\Kexts\ECEnabler.kext" "ECEnabler.kext (Bateria)"
Check-File "OC\Kexts\BrightnessKeys.kext" "BrightnessKeys.kext"
Check-File "OC\Kexts\SMCLightSensor.kext" "SMCLightSensor.kext" $false
Check-File "OC\Kexts\VoodooI2C.kext" "VoodooI2C.kext (Trackpad)" $false
Check-File "OC\Kexts\VoodooI2CHID.kext" "VoodooI2CHID.kext (Trackpad)" $false

# --- Kexts Rede ---
Write-Host "`nKEXTS REDE:" -ForegroundColor White
Check-File "OC\Kexts\RealtekRTL8111.kext" "RealtekRTL8111.kext (Ethernet)" $false
Check-File "OC\Kexts\AirportItlwm.kext" "AirportItlwm.kext (Wi-Fi Intel)" $false
Check-File "OC\Kexts\IntelBluetoothFirmware.kext" "IntelBluetoothFirmware.kext" $false
Check-File "OC\Kexts\IntelBTPatcher.kext" "IntelBTPatcher.kext" $false
Check-File "OC\Kexts\BlueToolFixup.kext" "BlueToolFixup.kext" $false

# --- Kexts Monitoramento ---
Write-Host "`nKEXTS MONITORAMENTO:" -ForegroundColor White
Check-File "OC\Kexts\SMCProcessorAMD.kext" "SMCProcessorAMD.kext" $false
Check-File "OC\Kexts\SMCRadeonSensors.kext" "SMCRadeonSensors.kext" $false

# --- Config ---
Write-Host "`nCONFIGURAÇÃO:" -ForegroundColor White
Check-File "OC\config.plist" "config.plist"

# --- Recovery ---
Write-Host "`nRECOVERY:" -ForegroundColor White
$recoveryDir = Join-Path (Split-Path $EfiDir -Parent) "com.apple.recovery.boot"
if (Test-Path (Join-Path $recoveryDir "BaseSystem.dmg")) {
    Write-Host "  [OK] BaseSystem.dmg" -ForegroundColor Green
}
elseif (Test-Path (Join-Path $recoveryDir "RecoveryImage.dmg")) {
    Write-Host "  [OK] RecoveryImage.dmg" -ForegroundColor Green
}
else {
    Write-Host "  [AVISO] Nenhum arquivo de recovery encontrado" -ForegroundColor Yellow
    Write-Host "         Execute baixar-macos-recovery.bat" -ForegroundColor Yellow
    $warnings++
}

# --- Resumo ---
Write-Host "`n=============================================" -ForegroundColor Cyan
if ($errors -eq 0 -and $warnings -eq 0) {
    Write-Host " TUDO PERFEITO! EFI está completa." -ForegroundColor Green
}
elseif ($errors -eq 0) {
    Write-Host " EFI OK com $warnings aviso(s)" -ForegroundColor Yellow
}
else {
    Write-Host " $errors ERRO(S) encontrado(s), $warnings aviso(s)" -ForegroundColor Red
    Write-Host " Corrija os erros antes de tentar bootar!" -ForegroundColor Red
}
Write-Host "=============================================" -ForegroundColor Cyan

Write-Host "`nLEMBRETES:" -ForegroundColor Yellow
Write-Host "  1. Editar config.plist com ProperTree (OC Snapshot)" -ForegroundColor Gray
Write-Host "  2. Mesclar AMD Vanilla patches (kernel patches)" -ForegroundColor Gray
Write-Host "  3. Alterar core count para 08 nos patches cpuid_cores_per_package" -ForegroundColor Gray
Write-Host "  4. Gerar SMBIOS com GenSMBIOS (MacBookPro16,2)" -ForegroundColor Gray
Write-Host "  5. Mapear USB com USBToolBox" -ForegroundColor Gray
Write-Host "  6. Configurar BIOS (Secure Boot OFF, AHCI, VRAM 512MB+)" -ForegroundColor Gray
