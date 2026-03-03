param(
    [string]$OutputDir = "$PSScriptRoot\HackintoshEFI",
    [string]$MacOSVersion = "sonoma"
)

$ErrorActionPreference = "Stop"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Hackintosh EFI Builder - Ryzen 4800HS" -ForegroundColor Cyan
Write-Host " ASUS Vivobook + NootedRed" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

function Get-LatestGitHubRelease {
    param([string]$Repo, [string]$AssetPattern)
    $apiUrl = "https://api.github.com/repos/$Repo/releases/latest"
    try {
        $release = Invoke-RestMethod -Uri $apiUrl -Headers @{ "User-Agent" = "PowerShell" }
        $asset = $release.assets | Where-Object { $_.name -match $AssetPattern } | Select-Object -First 1
        if ($asset) {
            return @{ Url = $asset.browser_download_url; Name = $asset.name; Version = $release.tag_name }
        }
    }
    catch {
        Write-Warning "Falha ao buscar release de $Repo"
    }
    return $null
}

function Download-File {
    param([string]$Url, [string]$Destination)
    $dir = Split-Path $Destination -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $fname = Split-Path $Url -Leaf
    Write-Host "  Baixando: $fname" -ForegroundColor Gray
    try {
        Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing
    }
    catch {
        Write-Warning "  FALHA ao baixar: $Url"
    }
}

function Extract-KextFromZip {
    param([string]$ZipPath, [string]$KextPattern, [string]$DestDir)
    $tempDir = Join-Path $env:TEMP "hackintosh_extract_$(Get-Random)"
    try {
        Expand-Archive -Path $ZipPath -DestinationPath $tempDir -Force
        $kexts = Get-ChildItem -Path $tempDir -Recurse -Directory | Where-Object { $_.Name -match $KextPattern -and $_.Name -like "*.kext" }
        foreach ($kext in $kexts) {
            $dest = Join-Path $DestDir $kext.Name
            if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
            Copy-Item $kext.FullName -Destination $dest -Recurse
            Write-Host "    Extraido: $($kext.Name)" -ForegroundColor Green
        }
    }
    finally {
        if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
    }
}

Write-Host "[1/7] Criando estrutura de diretorios..." -ForegroundColor Yellow

$efiDir = Join-Path $OutputDir "EFI"
$bootDir = Join-Path $efiDir "BOOT"
$ocDir = Join-Path $efiDir "OC"
$acpiDir = Join-Path $ocDir "ACPI"
$driversDir = Join-Path $ocDir "Drivers"
$kextsDir = Join-Path $ocDir "Kexts"
$toolsDir = Join-Path $ocDir "Tools"
$resourcesDir = Join-Path $ocDir "Resources"
$dlDir = Join-Path $OutputDir "_downloads"
$recoveryDir = Join-Path $OutputDir "com.apple.recovery.boot"

$dirs = @($bootDir, $acpiDir, $driversDir, $kextsDir, $toolsDir, $resourcesDir, $dlDir, $recoveryDir)
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}
Write-Host "  Estrutura criada em: $OutputDir" -ForegroundColor Green

Write-Host ""
Write-Host "[2/7] Baixando OpenCorePkg..." -ForegroundColor Yellow

$oc = Get-LatestGitHubRelease -Repo "acidanthera/OpenCorePkg" -AssetPattern "OpenCore-.*-RELEASE\.zip$"
if ($oc) {
    $ocZip = Join-Path $dlDir $oc.Name
    Download-File -Url $oc.Url -Destination $ocZip

    $ocExtract = Join-Path $dlDir "OpenCorePkg"
    if (Test-Path $ocExtract) { Remove-Item $ocExtract -Recurse -Force }
    Expand-Archive -Path $ocZip -DestinationPath $ocExtract -Force

    $bootEfi = Get-ChildItem -Path $ocExtract -Recurse -Filter "BOOTx64.efi" | Where-Object { $_.FullName -match "X64" } | Select-Object -First 1
    if ($bootEfi) { Copy-Item $bootEfi.FullName -Destination (Join-Path $bootDir "BOOTx64.efi") -Force }

    $ocEfi = Get-ChildItem -Path $ocExtract -Recurse -Filter "OpenCore.efi" | Where-Object { $_.FullName -match "X64" } | Select-Object -First 1
    if ($ocEfi) { Copy-Item $ocEfi.FullName -Destination (Join-Path $ocDir "OpenCore.efi") -Force }

    $runtimeEfi = Get-ChildItem -Path $ocExtract -Recurse -Filter "OpenRuntime.efi" | Where-Object { $_.FullName -match "X64" } | Select-Object -First 1
    if ($runtimeEfi) { Copy-Item $runtimeEfi.FullName -Destination (Join-Path $driversDir "OpenRuntime.efi") -Force }

    $shellEfi = Get-ChildItem -Path $ocExtract -Recurse -Filter "OpenShell.efi" | Where-Object { $_.FullName -match "X64" } | Select-Object -First 1
    if ($shellEfi) { Copy-Item $shellEfi.FullName -Destination (Join-Path $toolsDir "OpenShell.efi") -Force }

    $nvramEfi = Get-ChildItem -Path $ocExtract -Recurse -Filter "ResetNvramEntry.efi" | Where-Object { $_.FullName -match "X64" } | Select-Object -First 1
    if ($nvramEfi) { Copy-Item $nvramEfi.FullName -Destination (Join-Path $driversDir "ResetNvramEntry.efi") -Force }

    $samplePlist = Get-ChildItem -Path $ocExtract -Recurse -Filter "Sample.plist" | Select-Object -First 1
    if ($samplePlist) { Copy-Item $samplePlist.FullName -Destination (Join-Path $ocDir "config.plist") -Force }

    $macrecoverySource = Get-ChildItem -Path $ocExtract -Recurse -Directory -Filter "macrecovery" | Select-Object -First 1
    if ($macrecoverySource) {
        $macrecoveryDest = Join-Path $OutputDir "macrecovery"
        if (Test-Path $macrecoveryDest) { Remove-Item $macrecoveryDest -Recurse -Force }
        Copy-Item $macrecoverySource.FullName -Destination $macrecoveryDest -Recurse
    }

    Write-Host "  OpenCore $($oc.Version) instalado" -ForegroundColor Green
}

Write-Host ""
Write-Host "[3/7] Baixando HfsPlus.efi..." -ForegroundColor Yellow

$hfsPlusUrl = "https://github.com/acidanthera/OcBinaryData/raw/master/Drivers/HfsPlus.efi"
Download-File -Url $hfsPlusUrl -Destination (Join-Path $driversDir "HfsPlus.efi")
Write-Host "  HfsPlus.efi instalado" -ForegroundColor Green

Write-Host ""
Write-Host "[4/7] Baixando Kexts..." -ForegroundColor Yellow

$kextList = @(
    @{ Repo = "acidanthera/Lilu"; Pattern = "Lilu-.*-RELEASE\.zip$"; KextNames = @("Lilu") },
    @{ Repo = "acidanthera/VirtualSMC"; Pattern = "VirtualSMC-.*-RELEASE\.zip$"; KextNames = @("VirtualSMC", "SMCBatteryManager", "SMCLightSensor") },
    @{ Repo = "ChefKissInc/NootedRed"; Pattern = "NootedRed.*\.zip$"; KextNames = @("NootedRed") },
    @{ Repo = "acidanthera/AppleALC"; Pattern = "AppleALC-.*-RELEASE\.zip$"; KextNames = @("AppleALC") },
    @{ Repo = "acidanthera/NVMeFix"; Pattern = "NVMeFix-.*-RELEASE\.zip$"; KextNames = @("NVMeFix") },
    @{ Repo = "Mieze/RTL8111_driver_for_OS_X"; Pattern = "RealtekRTL8111.*\.zip$"; KextNames = @("RealtekRTL8111") },
    @{ Repo = "acidanthera/VoodooPS2"; Pattern = "VoodooPS2Controller-.*-RELEASE\.zip$"; KextNames = @("VoodooPS2Controller") },
    @{ Repo = "VoodooI2C/VoodooI2C"; Pattern = "VoodooI2C.*\.zip$"; KextNames = @("VoodooI2C", "VoodooI2CHID") },
    @{ Repo = "acidanthera/BrcmPatchRAM"; Pattern = "BrcmPatchRAM-.*-RELEASE\.zip$"; KextNames = @("BlueToolFixup") },
    @{ Repo = "OpenIntelWireless/itlwm"; Pattern = "AirportItlwm.*\.zip$"; KextNames = @("AirportItlwm") },
    @{ Repo = "OpenIntelWireless/IntelBluetoothFirmware"; Pattern = "IntelBluetoothFirmware.*\.zip$"; KextNames = @("IntelBluetoothFirmware", "IntelBTPatcher") },
    @{ Repo = "ChefKissInc/ForgedInvariant"; Pattern = "ForgedInvariant.*\.zip$"; KextNames = @("ForgedInvariant") },
    @{ Repo = "acidanthera/RestrictEvents"; Pattern = "RestrictEvents-.*-RELEASE\.zip$"; KextNames = @("RestrictEvents") },
    @{ Repo = "1Revenger1/ECEnabler"; Pattern = "ECEnabler-.*-RELEASE\.zip$"; KextNames = @("ECEnabler") },
    @{ Repo = "acidanthera/BrightnessKeys"; Pattern = "BrightnessKeys-.*-RELEASE\.zip$"; KextNames = @("BrightnessKeys") },
    @{ Repo = "ChefKissInc/SMCRadeonSensors"; Pattern = "SMCRadeonSensors.*\.zip$"; KextNames = @("SMCRadeonSensors") },
    @{ Repo = "Lorys89/SMCProcessorAMD"; Pattern = "SMCProcessorAMD.*\.zip$"; KextNames = @("SMCProcessorAMD") }
)

foreach ($kext in $kextList) {
    Write-Host "  > $($kext.Repo)..." -ForegroundColor Gray
    $release = Get-LatestGitHubRelease -Repo $kext.Repo -AssetPattern $kext.Pattern
    if ($release) {
        $zipPath = Join-Path $dlDir $release.Name
        Download-File -Url $release.Url -Destination $zipPath
        foreach ($kextName in $kext.KextNames) {
            Extract-KextFromZip -ZipPath $zipPath -KextPattern "^$kextName\.kext$" -DestDir $kextsDir
        }
    }
    else {
        Write-Warning "  Nao foi possivel encontrar release para $($kext.Repo)"
    }
}

Write-Host "  > AppleMCEReporterDisabler..." -ForegroundColor Gray
$mceUrl = "https://chefkiss.dev/Extras/Kexts/AppleMCEReporterDisabler.zip"
$mceZip = Join-Path $dlDir "AppleMCEReporterDisabler.zip"
Download-File -Url $mceUrl -Destination $mceZip
Extract-KextFromZip -ZipPath $mceZip -KextPattern "AppleMCEReporterDisabler\.kext" -DestDir $kextsDir

Write-Host "  Todos os kexts baixados!" -ForegroundColor Green

Write-Host ""
Write-Host "[5/7] Baixando SSDTs..." -ForegroundColor Yellow

$ssdtUrls = @(
    @{ Url = "https://chefkiss.dev/Extras/SSDTs/SSDT-PNLF.aml"; Name = "SSDT-PNLF.aml" },
    @{ Url = "https://chefkiss.dev/Extras/SSDTs/SSDT-ALS0.aml"; Name = "SSDT-ALS0.aml" }
)

foreach ($ssdt in $ssdtUrls) {
    Download-File -Url $ssdt.Url -Destination (Join-Path $acpiDir $ssdt.Name)
    Write-Host "    $($ssdt.Name)" -ForegroundColor Green
}

$ecdUrl = "https://github.com/dortania/Getting-Started-With-ACPI/raw/master/extra-files/compiled/SSDT-EC-USBX.aml"
Download-File -Url $ecdUrl -Destination (Join-Path $acpiDir "SSDT-EC-USBX.aml")
Write-Host "    SSDT-EC-USBX.aml" -ForegroundColor Green
Write-Host "  SSDTs instalados!" -ForegroundColor Green

Write-Host ""
Write-Host "[6/7] Baixando AMD Vanilla patches..." -ForegroundColor Yellow

$patchesUrl = "https://raw.githubusercontent.com/AMD-OSX/AMD_Vanilla/master/patches.plist"
$patchesPath = Join-Path $OutputDir "AMD_Vanilla_patches.plist"
Download-File -Url $patchesUrl -Destination $patchesPath
Write-Host "  patches.plist salvo em: $patchesPath" -ForegroundColor Green

Write-Host ""
Write-Host "[7/7] Resumo" -ForegroundColor Yellow
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " DOWNLOAD CONCLUIDO COM SUCESSO!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Estrutura EFI criada em: $efiDir" -ForegroundColor White
Write-Host ""
Write-Host "PROXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "  1. Baixar macOS Recovery com baixar-macos-recovery.bat" -ForegroundColor Gray
Write-Host "  2. Editar config.plist com ProperTree" -ForegroundColor Gray
Write-Host "  3. Gerar SMBIOS com GenSMBIOS - MacBookPro16,2" -ForegroundColor Gray
Write-Host "  4. Mapear USB com USBToolBox" -ForegroundColor Gray
Write-Host "  5. Copiar para pendrive com copiar-para-pendrive.ps1" -ForegroundColor Gray
Write-Host "  6. Configurar BIOS" -ForegroundColor Gray
Write-Host ""
Write-Host "Consulte: GUIA-HACKINTOSH-ASUS-VIVOBOOK-4800HS.md" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
