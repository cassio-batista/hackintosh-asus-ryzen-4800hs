#!/usr/bin/env python3
"""
Fix config.plist for ASUS Vivobook Ryzen 7 4800HS (Renoir) - COMPLETE FIX
Based on confirmed working configs:
  - ThinkPad T14s Gen 1 (Ryzen 7 PRO 4750U) - macOS Sequoia 15.7.3 SUCCESS
  - ThinkPad E14 Gen 2 (Ryzen 5 4600U) - Sequoia SUCCESS (AMD-OSX Discord fix)
"""

import plistlib
import shutil
import os

CONFIG_PATH = r'U:\EFI\OC\config.plist'
BACKUP_PATH = r'U:\EFI\OC\config.plist.bak3'

# Backup
shutil.copy2(CONFIG_PATH, BACKUP_PATH)
print('[OK] Backup criado: config.plist.bak3')

with open(CONFIG_PATH, 'rb') as f:
    config = plistlib.load(f)

fixes_applied = 0

# ============================================================
# FIX 1: BOOTER QUIRKS - Configuracao confirmada para Renoir
# Source: AMD-OSX Discord fix for 4600U + Dortania AMD Zen guide
# ============================================================
print('\n=== FIX 1: Booter Quirks para Renoir ===')

booter_changes = {
    'AvoidRuntimeDefrag': True,        # Padrao
    'DevirtualiseMmio': False,         # CRITICO: False para Renoir!
    'EnableSafeModeSlide': True,       # Padrao
    'EnableWriteUnprotector': True,    # CRITICO: True para Renoir!
    'ProtectUefiServices': False,      # Nao necessario para Renoir
    'ProvideCustomSlide': True,        # Padrao
    'RebuildAppleMemoryMap': False,    # CRITICO: False para Renoir!
    'SetupVirtualMap': True,           # Padrao para 17h
    'SyncRuntimePermissions': False,   # CRITICO: False para Renoir!
}

bq = config['Booter']['Quirks']
for key, val in booter_changes.items():
    old = bq.get(key)
    if old != val:
        bq[key] = val
        print('  [FIXED] %s: %s -> %s' % (key, old, val))
        fixes_applied += 1
    else:
        print('  [OK] %s: %s' % (key, val))

# ============================================================
# FIX 2: SMBIOS - MacBookPro16,2 (confirmado Renoir + NootedRed)
# Source: ThinkPad T14s Gen 1 SUCCESS post
# ============================================================
print('\n=== FIX 2: SMBIOS -> MacBookPro16,2 ===')

old_smbios = config['PlatformInfo']['Generic']['SystemProductName']
if old_smbios != 'MacBookPro16,2':
    config['PlatformInfo']['Generic']['SystemProductName'] = 'MacBookPro16,2'
    print('  [FIXED] SystemProductName: %s -> MacBookPro16,2' % old_smbios)
    fixes_applied += 1
else:
    print('  [OK] SystemProductName: MacBookPro16,2')

# ============================================================
# FIX 3: Desabilitar patches PAT duplicados (Shaneee)
# Manter apenas algrey habilitado. Shaneee e alternativo.
# ============================================================
print('\n=== FIX 3: Desabilitar patches Shaneee duplicados ===')

patches = config['Kernel']['Patch']
for i, p in enumerate(patches):
    comment = p.get('Comment', '')
    # Shaneee PAT patches should be disabled (algrey ones are the default)
    if 'Shaneee' in comment and p.get('Enabled', False):
        p['Enabled'] = False
        print('  [FIXED] Patch %d desabilitado: %s' % (i, comment[:70]))
        fixes_applied += 1
    # IOPCIIsHotplugPort - AM5 only, NOT for Renoir
    if 'IOPCIIsHotplugPort' in comment and p.get('Enabled', False):
        p['Enabled'] = False
        print('  [FIXED] Patch %d desabilitado (AM5 only): %s' % (i, comment[:70]))
        fixes_applied += 1

# ============================================================
# FIX 4: Desabilitar VoodooInput duplicado
# VoodooI2C tem seu proprio VoodooInput, e VoodooPS2 tambem
# Manter o do VoodooI2C, desabilitar do VoodooPS2
# ============================================================
print('\n=== FIX 4: Remover VoodooInput duplicado ===')

kexts = config['Kernel']['Add']
voodooinput_count = 0
for i, k in enumerate(kexts):
    bp = k.get('BundlePath', '')
    if 'VoodooInput.kext' in bp and 'PlugIns' in bp:
        voodooinput_count += 1
        if voodooinput_count > 1 and k.get('Enabled', True):
            k['Enabled'] = False
            print('  [FIXED] Desabilitado VoodooInput duplicado em: %s' % bp)
            fixes_applied += 1
        elif voodooinput_count == 1:
            print('  [OK] Mantido VoodooInput em: %s' % bp)

if voodooinput_count <= 1:
    print('  [OK] Nenhum VoodooInput duplicado encontrado')

# ============================================================
# FIX 5: Boot-args - Limpar e otimizar
# ============================================================
print('\n=== FIX 5: Boot-args ===')

nv_guid = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
nv = config['NVRAM']['Add'][nv_guid]

# Boot args para install de Renoir (sem NootedRed)
new_bootargs = '-v keepsyms=1 debug=0x100 alcid=21 npci=0x3000 amfi_get_out_of_my_way=0x1 ipc_control_port_options=0'
old_bootargs = nv.get('boot-args', '')
if old_bootargs != new_bootargs:
    nv['boot-args'] = new_bootargs
    print('  [FIXED] boot-args atualizado')
    print('    Antigo: %s' % old_bootargs)
    print('    Novo:   %s' % new_bootargs)
    fixes_applied += 1
else:
    print('  [OK] boot-args: %s' % new_bootargs)

# ============================================================
# FIX 6: Verificar patches cpuid_cores_per_package
# Ryzen 7 4800HS = 8 cores -> 0x08
# ============================================================
print('\n=== FIX 6: Verificar core count patches ===')

for i, p in enumerate(patches):
    comment = p.get('Comment', '')
    if 'cpuid_cores_per_package' in comment.lower():
        repl = p.get('Replace', b'')
        repl_hex = repl.hex()
        # Check if core count byte is 0x08
        if len(repl) >= 2:
            core_byte = repl[1]
            if core_byte == 0x08:
                print('  [OK] Patch %d: core count = 8 (0x08) - %s' % (i, repl_hex))
            else:
                print('  [WARN] Patch %d: core count = %d (0x%02x) - precisa ser 8!' % (i, core_byte, core_byte))
        else:
            print('  [WARN] Patch %d: Replace muito curto: %s' % (i, repl_hex))

# ============================================================
# FIX 7: Garantir que Kernel Quirks estao corretos
# ============================================================
print('\n=== FIX 7: Kernel Quirks ===')

kernel_changes = {
    'DummyPowerManagement': True,     # Necessario para AMD
    'PanicNoKextDump': True,          # Debug
    'PowerTimeoutKernelPanic': True,  # Debug
    'ProvideCurrentCpuInfo': True,    # Necessario para patches unificados
    'XhciPortLimit': False,           # Desabilitado para macOS 11.3+
}

kq = config['Kernel']['Quirks']
for key, val in kernel_changes.items():
    old = kq.get(key)
    if old != val:
        kq[key] = val
        print('  [FIXED] %s: %s -> %s' % (key, old, val))
        fixes_applied += 1
    else:
        print('  [OK] %s: %s' % (key, val))

# Guarantee DummyPowerManagement is in Emulate section
emu = config['Kernel']['Emulate']
if not emu.get('DummyPowerManagement', False):
    emu['DummyPowerManagement'] = True
    print('  [FIXED] Kernel -> Emulate -> DummyPowerManagement: True')
    fixes_applied += 1

# ============================================================
# FIX 8: Misc -> Security 
# ============================================================
print('\n=== FIX 8: Misc Security ===')

sec = config['Misc']['Security']
sec_changes = {
    'SecureBootModel': 'Disabled',
    'DmgLoading': 'Any',
    'Vault': 'Optional',
    'ScanPolicy': 0,
    'AllowSetDefault': True,
}
for key, val in sec_changes.items():
    old = sec.get(key)
    if old != val:
        sec[key] = val
        print('  [FIXED] %s: %s -> %s' % (key, old, val))
        fixes_applied += 1
    else:
        print('  [OK] %s: %s' % (key, val))

# ============================================================
# FIX 9: Misc -> Debug (melhorar debug output)
# ============================================================
print('\n=== FIX 9: Misc Debug ===')

dbg = config['Misc']['Debug']
dbg_changes = {
    'AppleDebug': True,
    'ApplePanic': True,
    'DisableWatchDog': True,
    'Target': 67,
}
for key, val in dbg_changes.items():
    old = dbg.get(key)
    if old != val:
        dbg[key] = val
        print('  [FIXED] %s: %s -> %s' % (key, old, val))
        fixes_applied += 1
    else:
        print('  [OK] %s: %s' % (key, val))

# ============================================================
# FIX 10: UEFI Quirks
# ============================================================
print('\n=== FIX 10: UEFI Quirks ===')

uq = config['UEFI']['Quirks']
uq_changes = {
    'ReleaseUsbOwnership': True,  # Importante para ASUS laptops
}
for key, val in uq_changes.items():
    old = uq.get(key)
    if old != val:
        uq[key] = val
        print('  [FIXED] %s: %s -> %s' % (key, old, val))
        fixes_applied += 1
    else:
        print('  [OK] %s: %s' % (key, val))

# ============================================================
# FIX 11: NVRAM Delete - garantir que boot-args e csr sao resetados
# ============================================================
print('\n=== FIX 11: NVRAM Delete ===')

nv_delete = config.get('NVRAM', {}).get('Delete', {})
if nv_guid not in nv_delete:
    nv_delete[nv_guid] = []
delete_list = nv_delete[nv_guid]
needed = ['boot-args', 'csr-active-config']
for n in needed:
    if n not in delete_list:
        delete_list.append(n)
        print('  [FIXED] Adicionado %s ao NVRAM Delete' % n)
        fixes_applied += 1
    else:
        print('  [OK] %s ja esta no NVRAM Delete' % n)

# Make WriteFlash true
config['NVRAM']['WriteFlash'] = True

# ============================================================
# SAVE
# ============================================================
print('\n' + '=' * 60)
print('Total de correcoes aplicadas: %d' % fixes_applied)

with open(CONFIG_PATH, 'wb') as f:
    plistlib.dump(config, f)

print('[SALVO] config.plist atualizado em %s' % CONFIG_PATH)

# ============================================================
# VERIFICACAO FINAL
# ============================================================
print('\n=== VERIFICACAO FINAL ===')
with open(CONFIG_PATH, 'rb') as f:
    v = plistlib.load(f)

bq = v['Booter']['Quirks']
print('Booter Quirks:')
print('  DevirtualiseMmio: %s (deve ser False)' % bq['DevirtualiseMmio'])
print('  EnableWriteUnprotector: %s (deve ser True)' % bq['EnableWriteUnprotector'])
print('  RebuildAppleMemoryMap: %s (deve ser False)' % bq['RebuildAppleMemoryMap'])
print('  SyncRuntimePermissions: %s (deve ser False)' % bq['SyncRuntimePermissions'])
print('  ProtectUefiServices: %s (deve ser False)' % bq['ProtectUefiServices'])
print('  SetupVirtualMap: %s (deve ser True)' % bq['SetupVirtualMap'])

print()
print('SMBIOS: %s (deve ser MacBookPro16,2)' % v['PlatformInfo']['Generic']['SystemProductName'])
print('boot-args: %s' % v['NVRAM']['Add'][nv_guid]['boot-args'])

print()
enabled_patches = 0
disabled_patches = 0
for p in v['Kernel']['Patch']:
    if p.get('Enabled', False):
        enabled_patches += 1
    else:
        disabled_patches += 1
print('Patches: %d habilitados, %d desabilitados' % (enabled_patches, disabled_patches))

# Check for disabled kexts
disabled_kexts = [k['BundlePath'] for k in v['Kernel']['Add'] if not k.get('Enabled', True)]
print('Kexts desabilitados: %s' % disabled_kexts)

print()
print('=== PRONTO! Tente bootar novamente. ===')
