#!/usr/bin/env python3
"""
fix-pci-hang.py
===============
Correcao baseada em config.plist CONFIRMADO funcionando:
  ASUS TUF A15 - Ryzen 7 4800H (mesmo chip que 4800HS)
  macOS Ventura/Sonoma/Sequoia STABLE
  Repo: tican10302/HACKINTOSH-EFI-ASUS-TUF-A15-RYZEN-7-4800H

Correcoes aplicadas:
  1. ADD kernel patch: probeBusGated | Disable 10 bit tags (FIX PCI HANG)
  2. ADD kernel patches: Visual | Remove non-monotonic time panic (2 patches)
  3. ADD driver: OpenVariableRuntimeDxe.efi ANTES de OpenRuntime.efi (LoadEarly)
  4. SET OpenRuntime.efi LoadEarly=True
  5. ADD kernel quirks: PanicNoKextDump, PowerTimeoutKernelPanic, ProvideCurrentCpuInfo, DisableLinkeditJettison
  6. ADD revblock=media ao boot-args
  7. Configurar Booter Quirks para match com config confirmado
"""

import plistlib
import shutil
import os
import base64
from datetime import datetime

CONFIG_PATH = r"C:\Users\cassi\git\New folder\HackintoshEFI\EFI\OC\config.plist"
BACKUP_PATH = CONFIG_PATH + f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

print("=" * 70)
print("  FIX PCI HANG - Baseado em Config ASUS TUF A15 4800H Confirmado")
print("=" * 70)

# Backup
shutil.copy2(CONFIG_PATH, BACKUP_PATH)
print(f"\n[OK] Backup: {os.path.basename(BACKUP_PATH)}")

with open(CONFIG_PATH, 'rb') as f:
    config = plistlib.load(f)

changes = []

# ============================================================
# 1. ADD KERNEL PATCH: probeBusGated | Disable 10 bit tags
#    Este patch e CRITICO para AMD - previne hang no PCI enumeration
# ============================================================
patches = config['Kernel']['Patch']

# Verificar se ja existe
has_probeBusGated = any('probeBusGated' in p.get('Comment', '') or 'probeBusGated' in p.get('Base', '') for p in patches)

if not has_probeBusGated:
    patch_probeBus = {
        'Arch': 'x86_64',
        'Base': '__ZN11IOPCIBridge13probeBusGatedEP14probeBusParams',
        'Comment': 'CaseySJ | probeBusGated | Disable 10 bit tags | 12.0+',
        'Count': 1,
        'Enabled': True,
        'Find': base64.b64decode('4BFyAA=='),
        'Identifier': 'com.apple.iokit.IOPCIFamily',
        'Limit': 0,
        'Mask': base64.b64decode('8P//8A=='),
        'MaxKernel': '24.99.99',
        'MinKernel': '21.0.0',
        'Replace': base64.b64decode('AAADAA=='),
        'ReplaceMask': base64.b64decode('AAAPAA=='),
        'Skip': 0,
    }
    patches.append(patch_probeBus)
    changes.append("ADD patch: CaseySJ | probeBusGated | Disable 10 bit tags | 12.0+ [CRITICAL PCI FIX]")

# ============================================================
# 2. ADD KERNEL PATCHES: Remove non-monotonic time panic
#    Patches essenciais para AMD - previnem panics relacionados a TSC
# ============================================================
has_time_panic_1 = any('thread_quantum_expire' in p.get('Comment', '') for p in patches)
has_time_panic_2 = any('thread_invoke, thread_dispatch' in p.get('Comment', '') for p in patches)

if not has_time_panic_1:
    patch_time1 = {
        'Arch': 'x86_64',
        'Base': '',
        'Comment': 'Visual | thread_quantum_expire, thread_unblock, thread_invoke | Remove non-monotonic time panic | 12.0+',
        'Count': 3,
        'Enabled': True,
        'Find': base64.b64decode('SAAAAAIAAEgAAFgAAAAPAAAAAAA='),
        'Identifier': 'kernel',
        'Limit': 0,
        'Mask': base64.b64decode('/wAAD/////8AAP8AAAD/AAAAAAA='),
        'MaxKernel': '24.99.99',
        'MinKernel': '21.0.0',
        'Replace': base64.b64decode('AAAAAAAAAAAAAAAAAABmkGaQZpA='),
        'ReplaceMask': base64.b64decode('AAAAAAAAAAAAAAAAAAD///////8='),
        'Skip': 0,
    }
    patches.append(patch_time1)
    changes.append("ADD patch: Visual | thread_quantum_expire/thread_unblock/thread_invoke | Remove non-monotonic time panic")

if not has_time_panic_2:
    patch_time2 = {
        'Arch': 'x86_64',
        'Base': '',
        'Comment': 'Visual | thread_invoke, thread_dispatch | Remove non-monotonic time panic | 12.0+',
        'Count': 2,
        'Enabled': True,
        'Find': base64.b64decode('SAAAgAQAAA8AAAAAAA=='),
        'Identifier': 'kernel',
        'Limit': 0,
        'Mask': base64.b64decode('SAAA8P////8AAAAAAA=='),
        'MaxKernel': '24.99.99',
        'MinKernel': '21.0.0',
        'Replace': base64.b64decode('AAAAAAAAAGaQZpBmkA=='),
        'ReplaceMask': base64.b64decode('AAAAAAAAAP///////w=='),
        'Skip': 0,
    }
    patches.append(patch_time2)
    changes.append("ADD patch: Visual | thread_invoke/thread_dispatch | Remove non-monotonic time panic")

# ============================================================
# 3. UEFI DRIVERS: OpenVariableRuntimeDxe.efi ANTES de OpenRuntime.efi
#    Ambos com LoadEarly=True (OBRIGATORIO para ASUS AMD)
# ============================================================
drivers = config['UEFI']['Drivers']

# Verificar se ja existe OpenVariableRuntimeDxe
has_ovrd = any('OpenVariableRuntimeDxe' in d.get('Path', '') for d in drivers)

if not has_ovrd:
    # Encontrar indice do OpenRuntime.efi
    openruntime_idx = None
    for i, d in enumerate(drivers):
        if 'OpenRuntime' in d.get('Path', ''):
            openruntime_idx = i
            break
    
    ovrd_entry = {
        'Arguments': '',
        'Comment': 'OpenVariableRuntimeDxe.efi',
        'Enabled': True,
        'LoadEarly': True,
        'Path': 'OpenVariableRuntimeDxe.efi',
    }
    
    if openruntime_idx is not None:
        drivers.insert(openruntime_idx, ovrd_entry)
        changes.append(f"ADD driver: OpenVariableRuntimeDxe.efi (LoadEarly=True, ANTES de OpenRuntime)")
    else:
        drivers.insert(0, ovrd_entry)
        changes.append(f"ADD driver: OpenVariableRuntimeDxe.efi (LoadEarly=True, posicao 0)")

# Garantir que OpenRuntime.efi tem LoadEarly=True
for d in drivers:
    if 'OpenRuntime' in d.get('Path', '') and 'OpenVariable' not in d.get('Path', ''):
        if not d.get('LoadEarly', False):
            d['LoadEarly'] = True
            changes.append("SET OpenRuntime.efi LoadEarly=True")

# ============================================================
# 4. KERNEL QUIRKS
# ============================================================
kquirks = config['Kernel']['Quirks']

quirks_to_set = {
    'PanicNoKextDump': True,
    'PowerTimeoutKernelPanic': True,
    'ProvideCurrentCpuInfo': True,
    'DisableLinkeditJettison': True,
}

for key, value in quirks_to_set.items():
    if kquirks.get(key) != value:
        old = kquirks.get(key, 'N/A')
        kquirks[key] = value
        changes.append(f"Kernel.Quirks.{key}: {old} -> {value}")

# ============================================================
# 5. BOOT-ARGS: Adicionar revblock=media
# ============================================================
nvram_uuid = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
nvram_add = config['NVRAM']['Add'].setdefault(nvram_uuid, {})
current_args = nvram_add.get('boot-args', '')

# Adicionar revblock=media se nao existe
new_args = current_args
if 'revblock=media' not in current_args:
    new_args += ' revblock=media'
    
# Remover npci=0x3000 se presente (vamos testar sem primeiro, ou manter 0x2000)
# O config confirmado usa npci=0x3000 entao vamos manter
# Mas se nao esta la, nao adicionar

new_args = new_args.strip()
if new_args != current_args:
    nvram_add['boot-args'] = new_args
    changes.append(f"boot-args: '{current_args}' -> '{new_args}'")

# ============================================================
# 6. BOOTER QUIRKS - Ajustar para config confirmado ASUS
#    O config confirmado TUF A15 usa:
#    - AvoidRuntimeDefrag: False (incomum!)
#    - DevirtualiseMmio: True
#    - EnableWriteUnprotector: True
#    Mas nosso firmware pode ser diferente. Vamos usar configuracao hibrida
#    segura que funciona na maioria dos ASUS AMD.
# ============================================================
booter = config['Booter']['Quirks']

# Manter MAT-compatible que estava funcionando ate PCI
# O boot CHEGA ao PCI - entao o Booter esta OK!
# Nao mudar Booter Quirks - o problema e PCI, nao memory/boot
booter_info = {
    'AvoidRuntimeDefrag': booter.get('AvoidRuntimeDefrag'),
    'DevirtualiseMmio': booter.get('DevirtualiseMmio'),
    'EnableWriteUnprotector': booter.get('EnableWriteUnprotector'),
    'RebuildAppleMemoryMap': booter.get('RebuildAppleMemoryMap'),
    'SyncRuntimePermissions': booter.get('SyncRuntimePermissions'),
    'SetupVirtualMap': booter.get('SetupVirtualMap'),
}
print(f"\n  Booter Quirks (mantidos - boot chega ao PCI OK):")
for k, v in booter_info.items():
    print(f"    {k}: {v}")

# ============================================================
# 7. MISC - Security (confirmar)
# ============================================================
security = config['Misc']['Security']
if security.get('DmgLoading') != 'Any':
    security['DmgLoading'] = 'Any'
    changes.append("Misc.Security.DmgLoading -> Any")

# ============================================================
# 8. KERNEL BLOCK: IOSkywalkFamily (necessario para Sonoma 14.x)
# ============================================================
block = config['Kernel'].setdefault('Block', [])
has_skywalk_block = any('IOSkywalkFamily' in b.get('Identifier', '') for b in block)

if not has_skywalk_block:
    block_entry = {
        'Arch': 'Any',
        'Comment': 'Block IOSkywalkFamily for Sonoma+',
        'Enabled': True,
        'Identifier': 'com.apple.iokit.IOSkywalkFamily',
        'MaxKernel': '',
        'MinKernel': '23.0.0',
        'Strategy': 'Exclude',
    }
    block.append(block_entry)
    changes.append("ADD block: IOSkywalkFamily (Exclude, MinKernel 23.0.0)")

# ============================================================
# SALVAR
# ============================================================
with open(CONFIG_PATH, 'wb') as f:
    plistlib.dump(config, f)

print(f"\n[CORRECOES APLICADAS: {len(changes)}]")
for i, c in enumerate(changes, 1):
    print(f"  {i:2d}. {c}")

if not changes:
    print("  Nenhuma correcao necessaria!")

# ============================================================
# VERIFICACAO FINAL
# ============================================================
print("\n" + "=" * 70)
print("  VERIFICACAO FINAL COMPLETA")
print("=" * 70)

with open(CONFIG_PATH, 'rb') as f:
    v = plistlib.load(f)

# Booter
bq = v['Booter']['Quirks']
print(f"\n  [BOOTER QUIRKS]")
for key in ['AvoidRuntimeDefrag', 'DevirtualiseMmio', 'EnableWriteUnprotector',
            'RebuildAppleMemoryMap', 'SetupVirtualMap', 'SyncRuntimePermissions',
            'ProtectUefiServices', 'ProvideCustomSlide']:
    print(f"    {key}: {bq.get(key, 'N/A')}")

# UEFI Drivers
print(f"\n  [UEFI DRIVERS] (ordem importa!)")
for i, d in enumerate(v['UEFI']['Drivers']):
    le = "LoadEarly" if d.get('LoadEarly', False) else "Normal"
    en = "ON" if d.get('Enabled', True) else "OFF"
    print(f"    {i+1}. [{en}] {d['Path']} ({le})")

# Kernel Patches
print(f"\n  [KERNEL PATCHES]")
enabled_patches = []
disabled_patches = []
for p in v['Kernel']['Patch']:
    comment = p.get('Comment', 'N/A')
    if p.get('Enabled', True):
        enabled_patches.append(comment)
    else:
        disabled_patches.append(comment)
print(f"    Habilitados: {len(enabled_patches)}")
print(f"    Desabilitados: {len(disabled_patches)}")
# Mostrar patches criticos
for c in enabled_patches:
    if any(kw in c for kw in ['probeBusGated', 'non-monotonic', 'Visual']):
        print(f"    [NOVO] {c}")

# Kernel Quirks 
print(f"\n  [KERNEL QUIRKS]")
kq = v['Kernel']['Quirks']
for key in ['PanicNoKextDump', 'PowerTimeoutKernelPanic', 'ProvideCurrentCpuInfo',
            'DisableLinkeditJettison', 'DisableRtcChecksum']:
    print(f"    {key}: {kq.get(key, 'N/A')}")

# Kernel Block
print(f"\n  [KERNEL BLOCK]")
for b in v['Kernel'].get('Block', []):
    en = "ON" if b.get('Enabled', True) else "OFF"
    print(f"    [{en}] {b['Identifier']} ({b.get('Strategy', 'N/A')}) MinKernel={b.get('MinKernel', '')}")

# Kexts
print(f"\n  [KEXTS]")
enabled = sum(1 for k in v['Kernel']['Add'] if k.get('Enabled', True))
disabled = sum(1 for k in v['Kernel']['Add'] if not k.get('Enabled', True))
print(f"    Habilitados: {enabled}, Desabilitados: {disabled}")
for k in v['Kernel']['Add']:
    if not k.get('Enabled', True):
        print(f"    [OFF] {k['BundlePath']}")

# NVRAM
nv = v['NVRAM']['Add'][nvram_uuid]
print(f"\n  [NVRAM]")
print(f"    boot-args: {nv.get('boot-args', 'N/A')}")
print(f"    csr-active-config: {nv.get('csr-active-config', b'').hex()}")

# Security
sec = v['Misc']['Security']
print(f"\n  [SECURITY]")
print(f"    DmgLoading: {sec['DmgLoading']}")
print(f"    SecureBootModel: {sec['SecureBootModel']}")

# SMBIOS
pi = v['PlatformInfo']['Generic']
print(f"\n  [SMBIOS] {pi['SystemProductName']}")

# Debug
dbg = v['Misc']['Debug']
print(f"\n  [DEBUG]")
print(f"    Target: {dbg.get('Target', 0)}")
print(f"    AppleDebug: {dbg.get('AppleDebug')}")
print(f"    ApplePanic: {dbg.get('ApplePanic')}")

# Emulate
emu = v['Kernel'].get('Emulate', {})
print(f"\n  [EMULATE]")
print(f"    DummyPowerManagement: {emu.get('DummyPowerManagement')}")

# UEFI Quirks
uq = v['UEFI']['Quirks']
print(f"\n  [UEFI QUIRKS]")
print(f"    ReleaseUsbOwnership: {uq.get('ReleaseUsbOwnership')}")

print("\n" + "=" * 70)
print("  CONFIG.PLIST CORRIGIDO! Proximo: copiar para pendrive")
print("=" * 70)
