#!/usr/bin/env python3
"""
fix-config-definitivo.py
========================
Correcao DEFINITIVA do config.plist para ASUS Vivobook Ryzen 7 4800HS (Renoir).

Parte da copia LOCAL que tem Booter Quirks MAT-compativeis CORRETOS e aplica
TODAS as correcoes necessarias para boot do macOS Sonoma 14.7 via Recovery.

Historico de erros:
  Boot 1: AppleMCEReporterDisabler sem Info.plist -> CORRIGIDO
  Boot 2: Prohibited symbol (seguranca) -> CORRIGIDO (DmgLoading, SIP, AMFI)
  Boot 3: Kernel panic vm_map_delete -> CORRIGIDO (VoodooInput dup, Shaneee, IOPCIIsHotplugPort)
  Boot 4: OCB: StartImage failed - Aborted -> Booter Quirks errados (fix-renoir.py quebrou)

Esta correcao:
  - MANTEM Booter Quirks MAT-compativeis (corretos no local)
  - Aplica TODAS as correcoes de seguranca (DmgLoading, SIP, AMFI)
  - Desabilita kexts problematicos (NootedRed, SMCRadeonSensors, VoodooInput dup)
  - Remove RealtekRTL8111 (nao existe fisicamente)
  - Configura boot-args corretos para AMD Renoir
  - Configura UEFI quirks para USB boot
  - Configura debug/logging adequado
"""

import plistlib
import shutil
import os
from datetime import datetime

# Caminhos
CONFIG_PATH = r"C:\Users\cassi\git\New folder\HackintoshEFI\EFI\OC\config.plist"
BACKUP_PATH = CONFIG_PATH + f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

print("=" * 70)
print("  CORRECAO DEFINITIVA - config.plist para ASUS Vivobook 4800HS")
print("=" * 70)

# Backup
shutil.copy2(CONFIG_PATH, BACKUP_PATH)
print(f"\n[OK] Backup criado: {os.path.basename(BACKUP_PATH)}")

# Carregar
with open(CONFIG_PATH, 'rb') as f:
    config = plistlib.load(f)

changes = []

# ============================================================
# 1. BOOTER QUIRKS - Verificar que estao corretos (MAT-compatible)
# ============================================================
booter = config['Booter']['Quirks']
expected_booter = {
    'AvoidRuntimeDefrag': True,
    'DevirtualiseMmio': False,         # Nao necessario para Renoir
    'EnableSafeModeSlide': True,
    'EnableWriteUnprotector': False,    # DEVE ser False (MAT firmware)
    'ProtectUefiServices': False,       # Nao necessario para ASUS consumer
    'ProvideCustomSlide': True,
    'RebuildAppleMemoryMap': True,      # DEVE ser True (MAT firmware)
    'SetupVirtualMap': True,
    'SyncRuntimePermissions': True,     # DEVE ser True (MAT firmware)
}

for key, expected in expected_booter.items():
    current = booter.get(key)
    if current != expected:
        booter[key] = expected
        changes.append(f"Booter.Quirks.{key}: {current} -> {expected}")

# ============================================================
# 2. MISC - Security
# ============================================================
security = config['Misc']['Security']

if security.get('DmgLoading') != 'Any':
    old = security.get('DmgLoading')
    security['DmgLoading'] = 'Any'
    changes.append(f"Misc.Security.DmgLoading: {old} -> Any")

if security.get('SecureBootModel') != 'Disabled':
    old = security.get('SecureBootModel')
    security['SecureBootModel'] = 'Disabled'
    changes.append(f"Misc.Security.SecureBootModel: {old} -> Disabled")

if security.get('Vault') != 'Optional':
    old = security.get('Vault')
    security['Vault'] = 'Optional'
    changes.append(f"Misc.Security.Vault: {old} -> Optional")

# AllowSetDefault para poder selecionar boot entry
if not security.get('AllowSetDefault', False):
    security['AllowSetDefault'] = True
    changes.append("Misc.Security.AllowSetDefault -> True")

# ============================================================
# 3. MISC - Debug
# ============================================================
debug = config['Misc']['Debug']

if not debug.get('AppleDebug', False):
    debug['AppleDebug'] = True
    changes.append("Misc.Debug.AppleDebug -> True")

if not debug.get('ApplePanic', False):
    debug['ApplePanic'] = True
    changes.append("Misc.Debug.ApplePanic -> True")

if not debug.get('DisableWatchDog', False):
    debug['DisableWatchDog'] = True
    changes.append("Misc.Debug.DisableWatchDog -> True")

# Target 67 = full verbose logging to screen + file
if debug.get('Target', 0) != 67:
    old = debug.get('Target', 0)
    debug['Target'] = 67
    changes.append(f"Misc.Debug.Target: {old} -> 67")

# ============================================================
# 4. NVRAM - boot-args
# ============================================================
nvram_uuid = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
nvram_add = config['NVRAM']['Add'].setdefault(nvram_uuid, {})

# boot-args otimizado para AMD Renoir + instalacao
new_bootargs = '-v keepsyms=1 debug=0x100 alcid=21 npci=0x3000 amfi_get_out_of_my_way=0x1 ipc_control_port_options=0'
old_bootargs = nvram_add.get('boot-args', '')
if old_bootargs != new_bootargs:
    nvram_add['boot-args'] = new_bootargs
    changes.append(f"boot-args: '{old_bootargs}' -> '{new_bootargs}'")

# csr-active-config = FF0F0000 (SIP totalmente desabilitado)
new_csr = bytes([0xFF, 0x0F, 0x00, 0x00])
old_csr = nvram_add.get('csr-active-config', b'')
if old_csr != new_csr:
    nvram_add['csr-active-config'] = new_csr
    changes.append(f"csr-active-config: {old_csr.hex() if old_csr else 'N/A'} -> ff0f0000")

# prev-lang:kbd - Ingles US
nvram_add['prev-lang:kbd'] = b'en-US:0'

# ============================================================
# 5. SMBIOS - MacBookPro16,3 (correto para AMD laptop sem dGPU)
# ============================================================
generic = config['PlatformInfo']['Generic']
if generic.get('SystemProductName') != 'MacBookPro16,3':
    old = generic.get('SystemProductName')
    generic['SystemProductName'] = 'MacBookPro16,3'
    changes.append(f"SMBIOS: {old} -> MacBookPro16,3")

# ============================================================
# 6. KERNEL - Kexts
# ============================================================
kexts = config['Kernel']['Add']

# 6a. Remover RealtekRTL8111 (nao existe fisicamente no EFI)
original_count = len(kexts)
kexts[:] = [k for k in kexts if k.get('BundlePath', '') != 'RealtekRTL8111.kext']
if len(kexts) < original_count:
    changes.append("Removido RealtekRTL8111.kext da config (nao existe fisicamente)")

# 6b. Desabilitar NootedRed (para fase de instalacao)
for kext in kexts:
    bp = kext.get('BundlePath', '')
    
    if bp == 'NootedRed.kext' and kext.get('Enabled', True):
        kext['Enabled'] = False
        changes.append("DESABILITADO NootedRed.kext (instalar primeiro sem GPU accel)")
    
    if bp == 'SMCRadeonSensors.kext' and kext.get('Enabled', True):
        kext['Enabled'] = False
        changes.append("DESABILITADO SMCRadeonSensors.kext (depende de NootedRed)")

# 6c. Desabilitar VoodooInput.kext DENTRO de VoodooI2C (duplicata com VoodooPS2)
for kext in kexts:
    bp = kext.get('BundlePath', '')
    if 'VoodooI2C.kext/Contents/PlugIns/VoodooInput.kext' in bp:
        if kext.get('Enabled', True):
            kext['Enabled'] = False
            changes.append("DESABILITADO VoodooInput.kext (duplicata dentro de VoodooI2C)")

# ============================================================
# 7. KERNEL - Patches (AMD Vanilla)
# ============================================================
patches = config['Kernel']['Patch']

for i, patch in enumerate(patches):
    comment = patch.get('Comment', '')
    
    # IOPCIIsHotplugPort - patch para AM5, nao necessario em Renoir
    if 'IOPCIIsHotplugPort' in comment:
        if patch.get('Enabled', True):
            patch['Enabled'] = False
            changes.append(f"DESABILITADO patch [{i}]: {comment}")
    
    # Shaneee PAT patches - conflitam com patches algrey padrao
    if 'Shaneee' in comment:
        if patch.get('Enabled', True):
            patch['Enabled'] = False
            changes.append(f"DESABILITADO patch [{i}]: {comment}")

# ============================================================
# 8. KERNEL - Emulate
# ============================================================
emulate = config['Kernel'].setdefault('Emulate', {})
if not emulate.get('DummyPowerManagement', False):
    emulate['DummyPowerManagement'] = True
    changes.append("Kernel.Emulate.DummyPowerManagement -> True")

# ============================================================
# 9. UEFI - Quirks
# ============================================================
uefi_quirks = config['UEFI']['Quirks']

# ReleaseUsbOwnership - necessario para teclado/mouse USB no boot
if not uefi_quirks.get('ReleaseUsbOwnership', False):
    uefi_quirks['ReleaseUsbOwnership'] = True
    changes.append("UEFI.Quirks.ReleaseUsbOwnership -> True")

# ============================================================
# 10. MISC - Boot
# ============================================================
boot = config['Misc'].setdefault('Boot', {})
if boot.get('HideAuxiliary', False):
    boot['HideAuxiliary'] = False
    changes.append("Misc.Boot.HideAuxiliary -> False (mostrar todas as entradas)")

# ============================================================
# SALVAR
# ============================================================
with open(CONFIG_PATH, 'wb') as f:
    plistlib.dump(config, f)

print(f"\n[CORRECOES APLICADAS: {len(changes)}]")
for i, c in enumerate(changes, 1):
    print(f"  {i:2d}. {c}")

if not changes:
    print("  Nenhuma correcao necessaria - config ja esta correto!")

# ============================================================
# VERIFICACAO FINAL
# ============================================================
print("\n" + "=" * 70)
print("  VERIFICACAO FINAL")
print("=" * 70)

with open(CONFIG_PATH, 'rb') as f:
    verify = plistlib.load(f)

bq = verify['Booter']['Quirks']
print(f"\n  Booter Quirks (MAT-compatible):")
print(f"    EnableWriteUnprotector: {bq['EnableWriteUnprotector']} (DEVE ser False)")
print(f"    RebuildAppleMemoryMap:  {bq['RebuildAppleMemoryMap']} (DEVE ser True)")
print(f"    SyncRuntimePermissions: {bq['SyncRuntimePermissions']} (DEVE ser True)")
print(f"    DevirtualiseMmio:       {bq['DevirtualiseMmio']} (DEVE ser False)")
print(f"    SetupVirtualMap:        {bq['SetupVirtualMap']} (DEVE ser True)")

sec = verify['Misc']['Security']
print(f"\n  Security:")
print(f"    DmgLoading:      {sec['DmgLoading']} (DEVE ser Any)")
print(f"    SecureBootModel:  {sec['SecureBootModel']} (DEVE ser Disabled)")

nv = verify['NVRAM']['Add'][nvram_uuid]
print(f"\n  NVRAM:")
print(f"    boot-args: {nv.get('boot-args')}")
print(f"    csr-active-config: {nv.get('csr-active-config', b'').hex()}")

pi = verify['PlatformInfo']['Generic']
print(f"\n  SMBIOS: {pi['SystemProductName']}")

# Contar kexts habilitados/desabilitados
enabled = sum(1 for k in verify['Kernel']['Add'] if k.get('Enabled', True))
disabled = sum(1 for k in verify['Kernel']['Add'] if not k.get('Enabled', True))
print(f"\n  Kexts: {enabled} habilitados, {disabled} desabilitados")
for k in verify['Kernel']['Add']:
    status = "ON " if k.get('Enabled', True) else "OFF"
    print(f"    [{status}] {k['BundlePath']}")

# Contar patches
pen = sum(1 for p in verify['Kernel']['Patch'] if p.get('Enabled', True))
pdis = sum(1 for p in verify['Kernel']['Patch'] if not p.get('Enabled', True))
print(f"\n  Patches: {pen} habilitados, {pdis} desabilitados")
for p in verify['Kernel']['Patch']:
    if not p.get('Enabled', True):
        print(f"    [OFF] {p.get('Comment', 'N/A')}")

print(f"\n  Debug Target: {verify['Misc']['Debug'].get('Target', 0)}")
print(f"  ReleaseUsbOwnership: {verify['UEFI']['Quirks'].get('ReleaseUsbOwnership')}")
print(f"  DummyPowerManagement: {verify['Kernel']['Emulate'].get('DummyPowerManagement')}")

print("\n" + "=" * 70)
print("  CONFIG.PLIST CORRIGIDO COM SUCESSO!")
print("  Proximo passo: conectar pendrive e copiar EFI")
print("=" * 70)
