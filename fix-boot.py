import plistlib

config_path = r'U:\EFI\OC\config.plist'
with open(config_path, 'rb') as f:
    config = plistlib.load(f)

print('=== APLICANDO CORRECOES ===')

# FIX 1: DmgLoading deve ser "Any" para Recovery funcionar sem problemas
# "Signed" pode bloquear o boot da Recovery em alguns casos
config['Misc']['Security']['DmgLoading'] = 'Any'
print('1. DmgLoading: Signed -> Any')

# FIX 2: csr-active-config - desabilitar SIP completamente para instalacao
# 0x0803 eh parcial, usar 0x7F0F0000 (totalmente desabilitado)
config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['csr-active-config'] = b'\xFF\x0F\x00\x00'
print('2. csr-active-config: 03080000 -> FF0F0000 (SIP totalmente desabilitado)')

# FIX 3: boot-args - adicionar amfi_get_out_of_my_way para AMFI nao bloquear
# e ipc_control_port_options=0 para evitar kernel panic em Sonoma
old_args = config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['boot-args']
new_args = '-v keepsyms=1 debug=0x100 alcid=21 npci=0x2000 amfi_get_out_of_my_way=0x1 ipc_control_port_options=0'
config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['boot-args'] = new_args
print('3. boot-args atualizado:')
print('   OLD:', old_args)
print('   NEW:', new_args)

# FIX 4: Desabilitar NootedRed para primeira instalacao
# NootedRed pode causar panic durante boot da Recovery
# Re-habilitar pos-instalacao
for k in config['Kernel']['Add']:
    bp = k.get('BundlePath', '')
    if 'NootedRed' in bp:
        k['Enabled'] = False
        print('4. NootedRed: DESABILITADO (pode causar panic no installer)')
    if 'SMCRadeonSensors' in bp:
        k['Enabled'] = False
        print('   SMCRadeonSensors: DESABILITADO (depende de NootedRed)')

# FIX 5: SMBIOS - MacBookPro16,3 pode ter issues com Sonoma Recovery
# Usar MacPro7,1 que e mais compativel com AMD barebone
# (NootedRed nao esta ativo entao sem risco de black screen)
config['PlatformInfo']['Generic']['SystemProductName'] = 'MacPro7,1'
print('5. SMBIOS: MacBookPro16,3 -> MacPro7,1 (melhor para AMD sem NootedRed)')

# FIX 6: Booter quirks para AMD Zen 2 / Renoir
# Alguns sistemas Zen 2 precisam de DevirtualiseMmio + ProtectUefiServices
config['Booter']['Quirks']['DevirtualiseMmio'] = True
config['Booter']['Quirks']['ProtectUefiServices'] = True
print('6. Booter: DevirtualiseMmio=True, ProtectUefiServices=True')

# FIX 7: Misc > Security - ExposeSensitiveData aumentar para debug
config['Misc']['Security']['ExposeSensitiveData'] = 15
print('7. ExposeSensitiveData: 6 -> 15')

# FIX 8: Verificar e corrigir patches AMD - garantir que todos estao habilitados
enabled_count = 0
disabled_count = 0
for p in config['Kernel']['Patch']:
    if p.get('Enabled', False):
        enabled_count += 1
    else:
        disabled_count += 1
print('8. AMD Patches: {} habilitados, {} desabilitados'.format(enabled_count, disabled_count))

# Habilitar todos os patches
for p in config['Kernel']['Patch']:
    p['Enabled'] = True
print('   Todos os 25 patches habilitados')

# FIX 9: Verificar core count patches
for p in config['Kernel']['Patch']:
    comment = p.get('Comment', '')
    if 'cpuid_cores_per_package' in comment.lower():
        rep = p.get('Replace', b'')
        print('   Core patch: {} -> Replace[1]=0x{:02X}'.format(
            comment.split('|')[-1].strip(), rep[1] if len(rep) > 1 else 0))

# Save
with open(config_path, 'wb') as f:
    plistlib.dump(config, f, sort_keys=False)

print('\n=== config.plist CORRIGIDO no pendrive! ===')
print('\nResumo das mudancas:')
print('  - DmgLoading: Any (permite boot Recovery)')
print('  - SIP: totalmente desabilitado')
print('  - AMFI: desabilitado via boot-args')
print('  - NootedRed: DESABILITADO (reabilitar pos-install)')
print('  - SMBIOS: MacPro7,1 (AMD compativel)')
print('  - Booter quirks otimizados para Zen 2')
print('  - Todos AMD Vanilla patches habilitados')
print('\nNOTA: Sem NootedRed, a resolucao sera baixa/generica.')
print('Apos instalar, reabilite NootedRed e troque SMBIOS para MacBookPro16,3.')
