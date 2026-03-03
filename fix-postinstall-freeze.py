import plistlib

config_path = r"C:\Users\cassi\git\New folder\efi_macos\EFI\OC\config.plist"
print(f"Modificando {config_path}...")

with open(config_path, 'rb') as f:
    config = plistlib.load(f)

# 1. Trazer o Verbose de volta (Tirar a escravidão da tela da maçã cega)
nvram_guid = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
boot_args = config['NVRAM']['Add'][nvram_guid].get('boot-args', '')
if '-v' not in boot_args:
    boot_args = '-v ' + boot_args
config['NVRAM']['Add'][nvram_guid]['boot-args'] = boot_args

# 2. Desabilitar kexts causadoras de congelamento no Sonoma
kexts_to_disable = [
    'SMCAMDProcessor',            # Trava o SMC em Mac AMD
    'AMDRyzenCPUPowerManagement', # Pode dar kernel panic de energia
    'AirportItlwm',               # Tem bug grave no Sonoma que congela na barra de loading
    'VoodooI2C',                  # Vou desligar temporariamente pra achar quem travou
    'VoodooI2CHID'
]

kexts_to_enable = [
    'itlwm.kext' # Substitui o Airport problemático (Não trava o boot)
]

for kx in config['Kernel']['Add']:
    path = kx['BundlePath']
    
    # Desabilitar as perigosas
    for disable_target in kexts_to_disable:
        if disable_target in path:
            kx['Enabled'] = False
            print(f"  - Desativado de Segurança: {path}")

    # Habilitar o Wi-Fi "Raiz" estável
    if path == 'itlwm.kext':
        kx['Enabled'] = True
        print(f"  + Re-ativado o Wi-Fi Seguro: {path}")

# Salvar
with open(config_path, 'wb') as f:
    plistlib.dump(config, f)

print(f"\nBoot-args restaurados para: {boot_args}")
print("Pronto para testar quem estava travando o Mac!")
