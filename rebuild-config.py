#!/usr/bin/env python3
"""
REBUILD CONFIG - Based on PROVEN WORKING TUF A15 4800H Reference
================================================================
This script rebuilds our config.plist to match the proven working
ASUS TUF A15 Ryzen 7 4800H configuration, adapted for our Vivobook.

Key changes from reference analysis:
1. Booter Quirks: AvoidRuntimeDefrag=False, EnableWriteUnprotector=True
2. Add missing SSDTs: SSDT-PLUG-ALT, SSDT-HPET, SSDT-XOSI
3. Add missing kexts: AMDRyzenCPUPowerManagement, AMFIPass
4. DisableRtcChecksum=True (important for ASUS boards)
5. ReleaseUsbOwnership=False (matches reference)
6. Fix GenericUSBXHCI nested directory structure
"""

import plistlib
import shutil
import os
import sys

def main():
    config_path = 'U:/EFI/OC/config.plist'
    ref_path = r'C:\Users\cassi\git\New folder\tuf-a15-ref\HACKINTOSH-EFI-ASUS-TUF-A15-RYZEN-7-4800H-main\EFI\OC\config.plist'
    ref_base = r'C:\Users\cassi\git\New folder\tuf-a15-ref\HACKINTOSH-EFI-ASUS-TUF-A15-RYZEN-7-4800H-main\EFI\OC'

    if not os.path.exists(config_path):
        print("ERRO: USB nao encontrado em U:")
        sys.exit(1)

    # Backup
    backup_path = config_path + '.bak-pre-rebuild'
    shutil.copy2(config_path, backup_path)
    print(f"[OK] Backup: {backup_path}")

    # Load configs
    with open(config_path, 'rb') as f:
        config = plistlib.load(f)
    with open(ref_path, 'rb') as f:
        ref = plistlib.load(f)

    changes = []

    # ==========================================================
    # 1. BOOTER QUIRKS - Match reference EXACTLY
    # ==========================================================
    booter_fixes = {
        'AvoidRuntimeDefrag': False,       # REF=False (was True)
        'EnableWriteUnprotector': True,     # REF=True (was False)
        'DevirtualiseMmio': True,           # Keep True (same as ref)
        'RebuildAppleMemoryMap': True,      # Keep True (same as ref)
        'SyncRuntimePermissions': True,     # Keep True (same as ref)
        'SetupVirtualMap': True,            # Keep True (same as ref)
        'ProvideCustomSlide': True,         # Keep
        'ProtectUefiServices': False,       # Keep False
    }
    for k, v in booter_fixes.items():
        old = config['Booter']['Quirks'].get(k)
        config['Booter']['Quirks'][k] = v
        if old != v:
            changes.append(f"[BOOTER] {k}: {old} -> {v}")

    # ==========================================================
    # 2. ACPI - Add missing SSDTs from reference
    # ==========================================================
    existing_ssdts = [a['Path'] for a in config['ACPI']['Add']]
    
    missing_ssdts = {
        'SSDT-PLUG-ALT.aml': 'AMD Ryzen CPU Power Management',
        'SSDT-HPET.aml': 'Fix IRQ Conflicts',
        'SSDT-XOSI.aml': 'OS Identification for macOS',
    }
    
    for ssdt_name, comment in missing_ssdts.items():
        if ssdt_name not in existing_ssdts:
            # Copy SSDT file from reference
            src = os.path.join(ref_base, 'ACPI', ssdt_name)
            dst = f'U:/EFI/OC/ACPI/{ssdt_name}'
            if os.path.exists(src):
                shutil.copy2(src, dst)
                # Add to config
                entry = {
                    'Comment': comment,
                    'Enabled': True,
                    'Path': ssdt_name,
                }
                config['ACPI']['Add'].append(entry)
                changes.append(f"[ACPI] Adicionado {ssdt_name} ({comment})")
            else:
                changes.append(f"[ACPI WARN] {ssdt_name} nao encontrado na referencia")

    # ==========================================================
    # 3. KERNEL QUIRKS
    # ==========================================================
    config['Kernel']['Quirks']['DisableRtcChecksum'] = True
    changes.append("[KERNEL] DisableRtcChecksum = True (ASUS boards)")

    # ==========================================================
    # 4. UEFI QUIRKS
    # ==========================================================
    config['UEFI']['Quirks']['ReleaseUsbOwnership'] = False
    changes.append("[UEFI] ReleaseUsbOwnership = False (matches reference)")

    # ==========================================================
    # 5. Add missing kexts from reference
    # ==========================================================
    kext_names = [k['BundlePath'] for k in config['Kernel']['Add']]
    
    # 5a. AMDRyzenCPUPowerManagement.kext
    if 'AMDRyzenCPUPowerManagement.kext' not in kext_names:
        src = os.path.join(ref_base, 'Kexts', 'AMDRyzenCPUPowerManagement.kext')
        dst = 'U:/EFI/OC/Kexts/AMDRyzenCPUPowerManagement.kext'
        if os.path.exists(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            entry = {
                'Arch': 'x86_64',
                'BundlePath': 'AMDRyzenCPUPowerManagement.kext',
                'Comment': 'AMD Ryzen CPU Power Management',
                'Enabled': True,
                'ExecutablePath': 'Contents/MacOS/AMDRyzenCPUPowerManagement',
                'MaxKernel': '',
                'MinKernel': '',
                'PlistPath': 'Contents/Info.plist',
            }
            # Insert after ForgedInvariant or near beginning
            insert_idx = len(config['Kernel']['Add'])
            for i, k in enumerate(config['Kernel']['Add']):
                if 'ForgedInvariant' in k.get('BundlePath', ''):
                    insert_idx = i + 1
                    break
            config['Kernel']['Add'].insert(insert_idx, entry)
            changes.append(f"[KEXT] Adicionado AMDRyzenCPUPowerManagement.kext @ {insert_idx}")
        else:
            changes.append("[KEXT WARN] AMDRyzenCPUPowerManagement.kext nao encontrado")

    # 5b. AMFIPass.kext
    if 'AMFIPass.kext' not in kext_names:
        src = os.path.join(ref_base, 'Kexts', 'AMFIPass.kext')
        dst = 'U:/EFI/OC/Kexts/AMFIPass.kext'
        if os.path.exists(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            entry = {
                'Arch': 'x86_64',
                'BundlePath': 'AMFIPass.kext',
                'Comment': 'AMFI Bypass',
                'Enabled': True,
                'ExecutablePath': 'Contents/MacOS/AMFIPass',
                'MaxKernel': '',
                'MinKernel': '',
                'PlistPath': 'Contents/Info.plist',
            }
            config['Kernel']['Add'].append(entry)
            changes.append(f"[KEXT] Adicionado AMFIPass.kext")
        else:
            changes.append("[KEXT WARN] AMFIPass.kext nao encontrado")

    # 5c. SMCAMDProcessor.kext (monitoring)
    if 'SMCAMDProcessor.kext' not in kext_names:
        src = os.path.join(ref_base, 'Kexts', 'SMCAMDProcessor.kext')
        dst = 'U:/EFI/OC/Kexts/SMCAMDProcessor.kext'
        if os.path.exists(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            entry = {
                'Arch': 'x86_64',
                'BundlePath': 'SMCAMDProcessor.kext',
                'Comment': 'AMD CPU Monitoring for VirtualSMC',
                'Enabled': True,
                'ExecutablePath': 'Contents/MacOS/SMCAMDProcessor',
                'MaxKernel': '',
                'MinKernel': '',
                'PlistPath': 'Contents/Info.plist',
            }
            # Insert after SMCProcessorAMD or SMCBatteryManager
            insert_idx = len(config['Kernel']['Add'])
            for i, k in enumerate(config['Kernel']['Add']):
                if 'SMCBatteryManager' in k.get('BundlePath', ''):
                    insert_idx = i + 1
                    break
            config['Kernel']['Add'].insert(insert_idx, entry)
            changes.append(f"[KEXT] Adicionado SMCAMDProcessor.kext @ {insert_idx}")

    # ==========================================================
    # 6. Remove SMCProcessorAMD (replaced by AMDRyzenCPUPowerManagement)
    # ==========================================================
    for kext in config['Kernel']['Add']:
        if 'SMCProcessorAMD' in kext.get('BundlePath', '') and kext.get('Enabled'):
            kext['Enabled'] = False
            changes.append("[KEXT] Desabilitado SMCProcessorAMD (substituido por AMDRyzenCPUPowerManagement)")

    # ==========================================================
    # 7. Fix UEFI Driver order - OpenVariableRuntimeDxe FIRST
    # ==========================================================
    drivers = config['UEFI']['Drivers']
    # Find OpenVariableRuntimeDxe and move to first position
    ovrd_idx = None
    for i, d in enumerate(drivers):
        path = d.get('Path', '') if isinstance(d, dict) else d
        if 'OpenVariableRuntimeDxe' in path:
            ovrd_idx = i
            break
    if ovrd_idx is not None and ovrd_idx > 0:
        ovrd = drivers.pop(ovrd_idx)
        drivers.insert(0, ovrd)
        changes.append("[UEFI] Movido OpenVariableRuntimeDxe.efi para PRIMEIRA posicao")

    # ==========================================================
    # 8. Boot-args cleanup (keep verbose, add keepsyms for debug)
    # ==========================================================
    nvram_guid = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
    boot_args = config['NVRAM']['Add'][nvram_guid].get('boot-args', '')
    
    # Remove msgbuf (not needed, causes issues sometimes)
    boot_args = boot_args.replace('msgbuf=1048576', '').strip()
    # Remove ipc_control_port_options (may cause issues)
    boot_args = boot_args.replace('ipc_control_port_options=0', '').strip()
    # Clean up multiple spaces
    while '  ' in boot_args:
        boot_args = boot_args.replace('  ', ' ')
    
    config['NVRAM']['Add'][nvram_guid]['boot-args'] = boot_args.strip()
    changes.append(f"[NVRAM] boot-args: {boot_args.strip()}")

    # ==========================================================
    # 9. Fix GenericUSBXHCI nested directory on USB
    # ==========================================================
    nested = 'U:/EFI/OC/Kexts/GenericUSBXHCI.kext/GenericUSBXHCI.kext'
    if os.path.exists(nested):
        shutil.rmtree(nested)
        changes.append("[FIX] Removido GenericUSBXHCI.kext aninhado duplicado")

    # ==========================================================
    # Print final state
    # ==========================================================
    print("\n=== KEXTS FINAL ===")
    for i, k in enumerate(config['Kernel']['Add']):
        status = "ON" if k.get('Enabled', False) else "OFF"
        print(f"  {i}: [{status}] {k.get('BundlePath', '')}")

    print(f"\n=== ACPI FINAL ===")
    for a in config['ACPI']['Add']:
        print(f"  {a['Path']} En={a['Enabled']}")

    print(f"\n=== UEFI DRIVERS (ordem) ===")
    for i, d in enumerate(config['UEFI']['Drivers']):
        path = d.get('Path', '') if isinstance(d, dict) else d
        le = d.get('LoadEarly', False) if isinstance(d, dict) else False
        print(f"  {i}: {path} (LoadEarly={le})")

    # Save
    with open(config_path, 'wb') as f:
        plistlib.dump(config, f)

    print(f"\n{'=' * 50}")
    print(f"{len(changes)} ALTERACOES APLICADAS:")
    print(f"{'=' * 50}")
    for c in changes:
        print(f"  {c}")

    print(f"\n[OK] config.plist RECONSTRUIDO em {config_path}")

if __name__ == '__main__':
    main()
