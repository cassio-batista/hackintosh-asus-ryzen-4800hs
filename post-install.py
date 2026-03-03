import plistlib

config_path = r"C:\Users\cassi\git\New folder\efi_macos\EFI\OC\config.plist"
print(f"Modificando {config_path}...")

with open(config_path, 'rb') as f:
    config = plistlib.load(f)

# 1. Limpar boot-args (Tirar Verbose e debug)
nvram_guid = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
boot_args = config['NVRAM']['Add'][nvram_guid].get('boot-args', '')
boot_args = boot_args.replace('-v', '').replace('debug=0x100', '').strip()
while '  ' in boot_args:
    boot_args = boot_args.replace('  ', ' ')
config['NVRAM']['Add'][nvram_guid]['boot-args'] = boot_args
print(f"Novos boot-args: {boot_args}")

# 2. Desligar logs e texto do OpenCore
config['Misc']['Debug']['AppleDebug'] = False
config['Misc']['Debug']['ApplePanic'] = False
config['Misc']['Debug']['Target'] = 0

# 3. Habilidades Pós-Instalação (Kexts Adicionais)
kexts_to_enable = [
    'SMCBatteryManager',          # Bateria
    'SMCAMDProcessor',            # Sensores Ryzen
    'AMDRyzenCPUPowerManagement', # Gerenciamento de Energia CPU
    'SMCLightSensor',             # Sensor de Luz
    'SMCProcessorAMD',            # Temperatura
    'SMCRadeonSensors',           # Monitoramento iGPU
    'AppleALC',                   # Áudio
    'AirportItlwm',               # Wi-Fi Nativo Apple UI
    'IntelBluetoothFirmware',     # Bluetooth
    'IntelBTPatcher',             # Patch Bluetooth
    'BlueToolFixup',              # Patch Bluetooth Sonoma
    'VoodooI2C',                  # Touchpad Master
    'VoodooI2CHID',               # Touchpad Gestos
    'ECEnabler',                  # Controlador de bateria BIOS
    'BrightnessKeys'              # Teclas de brilho F1/F2
]

for kx in config['Kernel']['Add']:
    path = kx['BundlePath']
    
    # Habilitar os kexts extras listados acima
    for enable_target in kexts_to_enable:
        if enable_target in path:
            kx['Enabled'] = True
            print(f"  + Habilitado: {path}")
            
    # Desabilitar o 'itlwm' puro que usava a senha presa no código
    if 'itlwm.kext' == path: # Igualdade exata para não pegar o AirportItlwm
        kx['Enabled'] = False
        print(f"  - Desabilitado (Removido): {path}")

# Salvar
with open(config_path, 'wb') as f:
    plistlib.dump(config, f)

print("\nConcluído! A EFI de pós-instalação está pronta.")
