import plistlib
import shutil
import urllib.request
import os
import zipfile

CONFIG_PATH = r"U:\EFI\OC\config.plist"
BACKUP_PATH = r"U:\EFI\OC\config.plist.bak.boot11"

print("="*60)
print(" PREPARING BOOT 11 FIXES: ASUS RENOIR 4800HS DEEP FIX")
print("="*60)

shutil.copy(CONFIG_PATH, BACKUP_PATH)

with open(CONFIG_PATH, 'rb') as f:
    config = plistlib.load(f)

changes = []

# 1. Booter Quirks - ASUS Specific
b = config['Booter']['Quirks']
b['SetupVirtualMap'] = True
b['DevirtualiseMmio'] = True
b['RebuildAppleMemoryMap'] = True
b['SyncRuntimePermissions'] = True
b['EnableWriteUnprotector'] = True
b['ProvideCustomSlide'] = True
b['EnableSafeModeSlide'] = True
changes.append("Booter Quirks configured specifically for ASUS BIOS (SetupVirtualMap=True, EnableWriteUnprotector=True)")

# 2. Kernel Quirks
k = config['Kernel']['Quirks']
k['ProvideCurrentCpuInfo'] = True
k['DisableRtcChecksum'] = True
k['PanicNoKextDump'] = True
k['PowerTimeoutKernelPanic'] = True
k['DisableLinkeditJettison'] = True
changes.append("Kernel Quirks configured (ProvideCurrentCpuInfo=True, DisableRtcChecksum=True)")

# Disable SMCAMDProcessor and AMDRyzenCPUPowerManagement if they exist
for kext in config['Kernel']['Add']:
    name = kext.get('BundlePath', '')
    if 'SMCAMDProcessor' in name or 'AMDRyzenCPUPowerManagement' in name:
        kext['Enabled'] = False
        changes.append(f"Disabled {name} for installation stability")
    if 'NootedRed' in name:
        kext['Enabled'] = True
        
# 3. Boot-args
nvram_guid = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
nvram = config['NVRAM']['Add'][nvram_guid]
args = nvram.get('boot-args', '')

new_args = ['npci=0x3000', '-wegnoegpu', 'revblock=media', '-NRedDPDelay']
for arg in new_args:
    if arg not in args:
        args += f" {arg}"

# Remove agdpmod if present
args = args.replace('agdpmod=pikera', '').strip()
nvram['boot-args'] = args
changes.append(f"Updated boot-args: {args}")

with open(CONFIG_PATH, 'wb') as f:
    plistlib.dump(config, f)

print("\nApplied changes:")
for c in changes:
    print(f"  - {c}")
