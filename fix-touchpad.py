import plistlib
import shutil

plist_path = 'efi_macos/EFI/OC/config.plist'
shutil.copy(plist_path, plist_path + '.backup')

with open(plist_path, 'rb') as f:
    config = plistlib.load(f)

# 1. Adicionar o patch _OSI to XOSI
osi_patch_exists = False
for patch in config['ACPI']['Patch']:
    if patch['Comment'] == 'Change _OSI to XOSI':
        osi_patch_exists = True
        patch['Enabled'] = True
        break

if not osi_patch_exists:
    config['ACPI']['Patch'].append({
        'Base': '',
        'BaseSkip': 0,
        'Comment': 'Change _OSI to XOSI',
        'Count': 0,
        'Enabled': True,
        'Find': b'_OSI',
        'Limit': 0,
        'Mask': b'',
        'OemTableId': b'',
        'Replace': b'XOSI',
        'ReplaceMask': b'',
        'Skip': 0,
        'TableLength': 0,
        'TableSignature': b'',
    })

# 2. Habilitar SSDT-XOSI.aml se existir, mas não estiver habilitado
for add in config['ACPI']['Add']:
    if add['Path'] == 'SSDT-XOSI.aml':
        add['Enabled'] = True

# 3. Adicionar -vi2c-force-polling para notebooks Asus/AMD que não suportam APIC interrupts bem
boot_args = config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['boot-args']
if '-vi2c-force-polling' not in boot_args:
    config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['boot-args'] = boot_args + ' -vi2c-force-polling'

# Garante que VoodooI2C e VoodooI2CHID fiquem ativados e o VoodooInput conflitante desabilitado
for kext in config['Kernel']['Add']:
    if kext['BundlePath'] in ['VoodooI2C.kext', 'VoodooI2C.kext/Contents/PlugIns/VoodooI2CServices.kext', 'VoodooI2C.kext/Contents/PlugIns/VoodooGPIO.kext', 'VoodooI2CHID.kext']:
        kext['Enabled'] = True
    if kext['BundlePath'] == 'VoodooI2C.kext/Contents/PlugIns/VoodooInput.kext':
        kext['Enabled'] = False

with open(plist_path, 'wb') as f:
    plistlib.dump(config, f)

print("Patch _OSI -> XOSI injetado.")
print("Argumento -vi2c-force-polling adicionado.")
print("Configurações do Touchpad 100% blindadas para AMD/ASUS!")