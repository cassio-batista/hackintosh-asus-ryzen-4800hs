"""
BOOT 12 - DEFINITIVE FIX
Based on CONFIRMED WORKING EFI: ASUS TUF A15 Ryzen 7 4800H
Source: github.com/tican10302/HACKINTOSH-EFI-ASUS-TUF-A15-RYZEN-7-4800H
Confirmed working: Ventura, Sonoma, Sequoia

KEY CHANGE: AvoidRuntimeDefrag = FALSE (critical for ASUS laptops with Renoir)
"""
import plistlib
import shutil

CONFIG_PATH = r"U:\EFI\OC\config.plist"
BACKUP_PATH = r"U:\EFI\OC\config.plist.bak.boot12"

shutil.copy(CONFIG_PATH, BACKUP_PATH)

with open(CONFIG_PATH, 'rb') as f:
    config = plistlib.load(f)

changes = []

# ═══════════════════════════════════════════════════════════
# 1. BOOTER QUIRKS - EXACT copy from confirmed working reference
# ═══════════════════════════════════════════════════════════
b = config['Booter']['Quirks']

# THE CRITICAL FIX: AvoidRuntimeDefrag must be FALSE on ASUS Renoir
b['AvoidRuntimeDefrag'] = False
changes.append("AvoidRuntimeDefrag = FALSE (CRITICAL: matches confirmed working TUF A15 EFI)")

b['DevirtualiseMmio'] = True
b['EnableSafeModeSlide'] = True
b['EnableWriteUnprotector'] = True
b['ProvideCustomSlide'] = True
b['RebuildAppleMemoryMap'] = True
b['SetupVirtualMap'] = True
b['SyncRuntimePermissions'] = True

# Ensure these are off
b['AllowRelocationBlock'] = False
b['DisableSingleUser'] = False
b['DisableVariableWrite'] = False
b['DiscardHibernateMap'] = False
b['ForceBooterSignature'] = False
b['ForceExitBootServices'] = False
b['ProtectMemoryRegions'] = False
b['ProtectSecureBoot'] = False
b['ProtectUefiServices'] = False
b['SignalAppleOS'] = False

changes.append("Booter Quirks: exact match to confirmed working TUF A15 reference")

# ═══════════════════════════════════════════════════════════
# 2. SMBIOS: Reference uses MacBookPro16,3
# ═══════════════════════════════════════════════════════════
old_smbios = config['PlatformInfo']['Generic']['SystemProductName']
config['PlatformInfo']['Generic']['SystemProductName'] = 'MacBookPro16,3'
changes.append(f"SMBIOS: {old_smbios} -> MacBookPro16,3 (matches reference)")

# ═══════════════════════════════════════════════════════════
# 3. UEFI Quirks: Add ExitBootServicesDelay as safety net
# ═══════════════════════════════════════════════════════════
config['UEFI']['Quirks']['ExitBootServicesDelay'] = 5
changes.append("ExitBootServicesDelay = 5 seconds (safety net for EXITBS)")

# ═══════════════════════════════════════════════════════════
# 4. Boot-args cleanup: remove -wegnoegpu (Vivobook has NO dGPU)
# ═══════════════════════════════════════════════════════════
nvram_guid = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
nvram = config['NVRAM']['Add'][nvram_guid]
args = nvram.get('boot-args', '')

# Remove -wegnoegpu (only needed if there's a discrete GPU to disable)
args = args.replace('-wegnoegpu', '').strip()

# Clean up any double spaces
while '  ' in args:
    args = args.replace('  ', ' ')

nvram['boot-args'] = args
changes.append(f"boot-args: {args}")

# ═══════════════════════════════════════════════════════════
# 5. Kernel Quirks: ensure all correct
# ═══════════════════════════════════════════════════════════
k = config['Kernel']['Quirks']
k['ProvideCurrentCpuInfo'] = True
k['PanicNoKextDump'] = True
k['PowerTimeoutKernelPanic'] = True
k['DisableLinkeditJettison'] = True
k['DisableRtcChecksum'] = True

# ═══════════════════════════════════════════════════════════
# 6. Kexts: Minimal set for boot (disable extras that can cause issues)
# ═══════════════════════════════════════════════════════════
for kx in config['Kernel']['Add']:
    name = kx.get('BundlePath', '')
    
    # These MUST be enabled
    must_enable = ['Lilu', 'VirtualSMC', 'NootedRed', 'AppleMCEReporter', 
                   'RestrictEvents', 'VoodooPS2', 'AMFIPass', 'ForgedInvariant',
                   'NVMeFix']
    
    # These should be DISABLED during initial install boot
    must_disable = ['SMCAMDProcessor', 'AMDRyzenCPU', 'SMCProcessorAMD',
                    'SMCRadeonSensors', 'AirportItlwm', 'IntelBluetooth',
                    'BlueToolFixup', 'GenericUSBXHCI', 'VoodooI2C',
                    'VoodooI2CHID', 'ECEnabler', 'BrightnessKeys',
                    'SMCBatteryManager', 'SMCLightSensor', 'AppleALC',
                    'RealtekRTL8111']
    
    for pattern in must_disable:
        if pattern in name and 'PlugIns' not in name:
            if kx['Enabled']:
                kx['Enabled'] = False
                changes.append(f"Disabled {name} (minimal boot)")
    
    # VoodooPS2 plugins should follow parent
    if 'VoodooPS2' in name:
        kx['Enabled'] = True

# Re-enable critical ones
for kx in config['Kernel']['Add']:
    name = kx.get('BundlePath', '')
    for pattern in must_enable:
        if pattern in name and 'PlugIns' not in name:
            kx['Enabled'] = True

# ═══════════════════════════════════════════════════════════
# WRITE
# ═══════════════════════════════════════════════════════════
with open(CONFIG_PATH, 'wb') as f:
    plistlib.dump(config, f)

print("=" * 60)
print(" BOOT 12: DEFINITIVE FIX APPLIED")
print(" Based on: ASUS TUF A15 Ryzen 7 4800H confirmed EFI")
print("=" * 60)
print()
for c in changes:
    print(f"  -> {c}")
print()

# Verify final state
with open(CONFIG_PATH, 'rb') as f:
    v = plistlib.load(f)

print("VERIFICATION:")
print(f"  AvoidRuntimeDefrag = {v['Booter']['Quirks']['AvoidRuntimeDefrag']}")
print(f"  SetupVirtualMap = {v['Booter']['Quirks']['SetupVirtualMap']}")
print(f"  DevirtualiseMmio = {v['Booter']['Quirks']['DevirtualiseMmio']}")
print(f"  EnableWriteUnprotector = {v['Booter']['Quirks']['EnableWriteUnprotector']}")
print(f"  RebuildAppleMemoryMap = {v['Booter']['Quirks']['RebuildAppleMemoryMap']}")
print(f"  SyncRuntimePermissions = {v['Booter']['Quirks']['SyncRuntimePermissions']}")
print(f"  ExitBootServicesDelay = {v['UEFI']['Quirks']['ExitBootServicesDelay']}")
print(f"  SystemProductName = {v['PlatformInfo']['Generic']['SystemProductName']}")
print()
print("KEXTS ENABLED:")
for kx in v['Kernel']['Add']:
    if kx['Enabled']:
        print(f"  + {kx['BundlePath']}")
print()
print("KEXTS DISABLED:")
for kx in v['Kernel']['Add']:
    if not kx['Enabled']:
        print(f"  - {kx['BundlePath']}")
