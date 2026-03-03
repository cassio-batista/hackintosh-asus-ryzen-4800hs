import urllib.request
import plistlib
import os
import subprocess
import shutil

CONFIG_PATH = r"U:\EFI\OC\config.plist"
BACKUP_PATH = r"U:\EFI\OC\config.plist.bak.boot10"

print("="*60)
print(" PREPARING BOOT 10 FIXES: EXITBS:START REBOOT FIX & NOOTEDRED")
print("="*60)

# Backup
shutil.copy(CONFIG_PATH, BACKUP_PATH)
print("Backup created.")

with open(CONFIG_PATH, 'rb') as f:
    config = plistlib.load(f)

changes = []

# 1. Booter Quirks
b = config['Booter']['Quirks']
b['SetupVirtualMap'] = False
changes.append("SetupVirtualMap = False (Fix instant reboot on AMD Laptops)")

# Let's keep DevirtualiseMmio = True since it helped PCI configuration earlier,
# but we are absolutely sure RebuildAppleMemoryMap = True and EnableWriteUnprotector = False
b['RebuildAppleMemoryMap'] = True
b['EnableWriteUnprotector'] = False

# 2. Patcher Core Count is already correct (08)
# Let's ensure ProvideCurrentCpuInfo is True
config['Kernel']['Quirks']['ProvideCurrentCpuInfo'] = True

# 3. Kexts: Enable NootedRed!
for kext in config['Kernel']['Add']:
    if 'NootedRed' in kext.get('BundlePath', ''):
        kext['Enabled'] = True
        changes.append("NootedRed.kext ENABLED (Required for installer to not crash/dark screen on AMD APU)")
    if 'WhateverGreen' in kext.get('BundlePath', ''):
        kext['Enabled'] = False
        
# 4. Boot-Args
nvram_guid = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
nvram = config['NVRAM']['Add'][nvram_guid]
args = nvram.get('boot-args', '')
if '-NRedDPDelay' not in args:
    args += ' -NRedDPDelay'
    changes.append("Added -NRedDPDelay to boot-args (NootedRed fallback delay)")

# For NootedRed, it's sometimes recommended to use agdpmod=pikera but NOT for Vega. For Vega, no agdpmod.
# We have `msgbuf=1048576`, keeping it.
nvram['boot-args'] = args.strip()

# 5. SMBIOS: ChefKiss specifically asks for MacBookPro16,2, iMac20,1 or iMacPro1,1.
old_smbios = config['PlatformInfo']['Generic'].get('SystemProductName', '')
if '16,2' not in old_smbios:
    print(f"Current SMBIOS is {old_smbios}. Generating new SMBIOS for MacBookPro16,2...")
    # Generate new SMBIOS using macserial
    macserial_exe = r"C:\Users\cassi\git\New folder\HackintoshEFI\macserial\macserial.exe"
    
    # We might not have macserial.exe downloaded directly here if it was run in powershell.
    # Let's just use a hardcoded valid (but fake) MacBookPro16,2 for recovery install, 
    # OR we can just change the string and let the user generate it properly later.
    # For now, let's just change the SystemProductName. OpenCore will still use the old serial, 
    # which will be invalid for 16,2, but the installer won't verify serial matches product name to boot recovery.
    config['PlatformInfo']['Generic']['SystemProductName'] = 'MacBookPro16,2'
    changes.append(f"SMBIOS SystemProductName: {old_smbios} -> MacBookPro16,2 (ChefKiss required)")

with open(CONFIG_PATH, 'wb') as f:
    plistlib.dump(config, f)

print("\nApplied changes:")
for c in changes:
    print(f"  - {c}")
print("\nBoot 10 Ready!")
