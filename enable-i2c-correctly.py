import plistlib
import sys

config_path = 'efi_macos/EFI/OC/config.plist'
with open(config_path, 'rb') as f:
    config = plistlib.load(f)

for kext in config['Kernel']['Add']:
    # Ativa I2C e seus componentes (exceto VoodooInput secundario)
    if kext['BundlePath'] in ['VoodooI2C.kext', 'VoodooI2C.kext/Contents/PlugIns/VoodooI2CServices.kext', 'VoodooI2C.kext/Contents/PlugIns/VoodooGPIO.kext', 'VoodooI2CHID.kext']:
        kext['Enabled'] = True
    # Garante que as VoodooInput filhas do VoodooI2C não carreguem,
    # deixando o controle para o VoodooInput de dentro do VoodooPS2Controller
    if kext['BundlePath'] == 'VoodooI2C.kext/Contents/PlugIns/VoodooInput.kext':
        kext['Enabled'] = False

with open(config_path, 'wb') as f:
    plistlib.dump(config, f)
print("Configurações do I2C atualizadas para evitar conflitos de VoodooInput.")