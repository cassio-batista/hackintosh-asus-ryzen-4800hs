import plistlib
import sys

config_path = 'efi_macos/EFI/OC/config.plist'
with open(config_path, 'rb') as f:
    config = plistlib.load(f)

# 1. Habilitar AirportItlwm e Desabilitar itlwm
for kext in config['Kernel']['Add']:
    if kext['BundlePath'] == 'AirportItlwm.kext':
        kext['Enabled'] = True
    if kext['BundlePath'] == 'itlwm.kext':
        kext['Enabled'] = False

# 2. Remover apenas o -v (verbose) dos boot-args para mostrar a Maçã
boot_args = config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['boot-args']
boot_args_list = boot_args.split()
if '-v' in boot_args_list:
    boot_args_list.remove('-v')
config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['boot-args'] = ' '.join(boot_args_list)

# 3. Remover também na seção de boot args alternativos, se houver, pra garantir
if 'NVRAM' in config and 'Add' in config['NVRAM'] and '7C436110-AB2A-4BBB-A880-FE41995C9F82' in config['NVRAM']['Add']:
   # Config já foi atualizada acima
   pass


with open(config_path, 'wb') as f:
    plistlib.dump(config, f)

print(f"Modificações feitas com sucesso:")
print(f"  - Wi-Fi Nativo (AirportItlwm): ATIVADO")
print(f"  - Wi-Fi Oculto (itlwm): DESATIVADO")
print(f"  - Verbose Mode (-v): REMOVIDO (A Maçã vai aparecer!)")
print(f"  - Novos boot-args: {' '.join(boot_args_list)}")