#!/usr/bin/env python3
"""
Fix Boot 7 - Comprehensive fix for IOTimeSyncRootService hang
=============================================================
Root cause analysis:
1. AirportItlwm.kext depends on IOSkywalkFamily (in OSBundleLibraries)
2. We blocked IOSkywalkFamily in Kernel Block
3. AirportItlwm injection FAILS with "Invalid Parameter" (16MB wasted)
4. IOTimeSyncFamily also depends on IOSkywalkFamily -> "Couldn't alloc class IOTimeSyncRootService"
5. The boot MAY hang due to AirportItlwm injection failure or USB issues

Fixes applied:
A) Disable AirportItlwm.kext (failing injection - not needed for install)
B) Disable IntelBluetoothFirmware.kext (not needed for install)
C) Disable IntelBTPatcher.kext (not needed for install)
D) Disable BlueToolFixup.kext (not needed for install)
E) Add GenericUSBXHCI.kext (AMD Ryzen USB XHCI support)
F) Add -msgbuf=1048576 to boot-args for more verbose output
G) Remove IOSkywalkFamily block (since AirportItlwm is disabled, no conflict)
   Actually KEEP the block - it prevents other issues on Sonoma
H) Ensure proper SMBIOS and booter quirks remain intact
"""

import plistlib
import shutil
import os
import sys

def main():
    # Determine config path
    config_path = 'U:/EFI/OC/config.plist'
    if not os.path.exists(config_path):
        print("ERRO: USB nao encontrado em U:")
        sys.exit(1)

    # Backup
    backup_path = config_path + '.bak-boot6'
    shutil.copy2(config_path, backup_path)
    print(f"[OK] Backup: {backup_path}")

    # Load config
    with open(config_path, 'rb') as f:
        config = plistlib.load(f)

    changes = []

    # =====================================================
    # A) Disable AirportItlwm.kext
    # =====================================================
    for kext in config['Kernel']['Add']:
        bp = kext.get('BundlePath', '')
        if 'AirportItlwm' in bp and kext.get('Enabled', False):
            kext['Enabled'] = False
            changes.append(f"[FIX-A] Desabilitado AirportItlwm.kext (falha injecao, depende IOSkywalkFamily bloqueado)")

    # =====================================================
    # B) Disable IntelBluetoothFirmware.kext
    # =====================================================
    for kext in config['Kernel']['Add']:
        bp = kext.get('BundlePath', '')
        if 'IntelBluetoothFirmware' in bp and kext.get('Enabled', False):
            kext['Enabled'] = False
            changes.append(f"[FIX-B] Desabilitado IntelBluetoothFirmware.kext (nao necessario para instalacao)")

    # =====================================================
    # C) Disable IntelBTPatcher.kext
    # =====================================================
    for kext in config['Kernel']['Add']:
        bp = kext.get('BundlePath', '')
        if 'IntelBTPatcher' in bp and kext.get('Enabled', False):
            kext['Enabled'] = False
            changes.append(f"[FIX-C] Desabilitado IntelBTPatcher.kext (nao necessario para instalacao)")

    # =====================================================
    # D) Disable BlueToolFixup.kext
    # =====================================================
    for kext in config['Kernel']['Add']:
        bp = kext.get('BundlePath', '')
        if 'BlueToolFixup' in bp and kext.get('Enabled', False):
            kext['Enabled'] = False
            changes.append(f"[FIX-D] Desabilitado BlueToolFixup.kext (nao necessario para instalacao)")

    # =====================================================
    # E) Add GenericUSBXHCI.kext (AMD Ryzen USB XHCI Fix)
    # =====================================================
    already_has_gux = any('GenericUSBXHCI' in k.get('BundlePath', '') for k in config['Kernel']['Add'])
    if not already_has_gux:
        gux_entry = {
            'Arch': 'x86_64',
            'BundlePath': 'GenericUSBXHCI.kext',
            'Comment': 'AMD Ryzen USB XHCI Fix v1.3.0b1',
            'Enabled': True,
            'ExecutablePath': 'Contents/MacOS/GenericUSBXHCI',
            'MaxKernel': '',
            'MinKernel': '',
            'PlistPath': 'Contents/Info.plist',
        }
        # Insert after RestrictEvents (index 26) but before AppleMCEReporterDisabler
        # Actually, insert it after all VirtualSMC/Lilu kexts but before VoodooPS2
        # Best: insert after ForgedInvariant (index 8) or after NVMeFix (index 9)
        insert_idx = None
        for i, k in enumerate(config['Kernel']['Add']):
            if 'NVMeFix' in k.get('BundlePath', ''):
                insert_idx = i + 1
                break
        if insert_idx is None:
            insert_idx = len(config['Kernel']['Add'])
        config['Kernel']['Add'].insert(insert_idx, gux_entry)
        changes.append(f"[FIX-E] Adicionado GenericUSBXHCI.kext @ index {insert_idx} (AMD Ryzen USB XHCI Fix)")
    else:
        changes.append("[INFO-E] GenericUSBXHCI.kext ja existe na config")

    # =====================================================
    # F) Add -msgbuf=1048576 to boot-args
    # =====================================================
    nvram_guid = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
    boot_args = config['NVRAM']['Add'][nvram_guid].get('boot-args', '')
    if 'msgbuf=' not in boot_args:
        boot_args = boot_args.strip() + ' msgbuf=1048576'
        config['NVRAM']['Add'][nvram_guid]['boot-args'] = boot_args
        changes.append(f"[FIX-F] Adicionado msgbuf=1048576 (buffer de mensagens maior para debug)")

    # =====================================================
    # G) Keep IOSkywalkFamily block (good for Sonoma stability)
    # =====================================================
    for block in config['Kernel']['Block']:
        if 'IOSkywalkFamily' in block.get('Identifier', ''):
            changes.append(f"[INFO-G] IOSkywalkFamily block mantido (Enabled={block.get('Enabled')})")

    # =====================================================
    # H) Verify critical settings remain correct
    # =====================================================
    booter = config['Booter']['Quirks']
    checks = {
        'AvoidRuntimeDefrag': True,
        'DevirtualiseMmio': True,
        'EnableWriteUnprotector': False,
        'RebuildAppleMemoryMap': True,
        'SyncRuntimePermissions': True,
        'SetupVirtualMap': True,
    }
    for key, expected in checks.items():
        actual = booter.get(key)
        status = "OK" if actual == expected else f"CORRIGIDO {actual}->{expected}"
        if actual != expected:
            booter[key] = expected
        changes.append(f"[CHECK-H] Booter {key}={expected} ({status})")

    # Verify SMBIOS
    smbios = config.get('PlatformInfo', {}).get('Generic', {}).get('SystemProductName', '')
    changes.append(f"[CHECK-H] SMBIOS: {smbios}")

    # Verify DummyPowerManagement
    dpm = config.get('Kernel', {}).get('Emulate', {}).get('DummyPowerManagement', False)
    changes.append(f"[CHECK-H] DummyPowerManagement: {dpm}")

    # =====================================================
    # EXTRA: Also disable AppleALC temporarily to reduce kext load
    # Actually NO - AppleALC is small and shouldn't cause issues
    # =====================================================

    # Print boot-args final
    final_args = config['NVRAM']['Add'][nvram_guid].get('boot-args', '')
    changes.append(f"[INFO] boot-args final: {final_args}")

    # Print kext summary
    print("\n=== KEXTS APOS CORRECOES ===")
    for i, k in enumerate(config['Kernel']['Add']):
        status = "ON" if k.get('Enabled', False) else "OFF"
        print(f"  {i}: [{status}] {k.get('BundlePath', '')}")

    # Save
    with open(config_path, 'wb') as f:
        plistlib.dump(config, f)

    print(f"\n=== {len(changes)} ALTERACOES APLICADAS ===")
    for c in changes:
        print(f"  {c}")

    print(f"\n[OK] config.plist salvo em {config_path}")
    print("\nPROXIMO PASSO: Copie GenericUSBXHCI.kext para U:\\EFI\\OC\\Kexts\\")

if __name__ == '__main__':
    main()
