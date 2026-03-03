import plistlib

config_path = 'efi_macos/EFI/OC/config.plist'
with open(config_path, 'rb') as f:
    config = plistlib.load(f)

# Reverter para itlwm (estável) e desativar AirportItlwm
for kext in config['Kernel']['Add']:
    if kext['BundlePath'] == 'AirportItlwm.kext':
        kext['Enabled'] = False
    elif kext['BundlePath'] == 'itlwm.kext':
        kext['Enabled'] = True

with open(config_path, 'wb') as f:
    plistlib.dump(config, f)

print("Revertido para itlwm com sucesso!")