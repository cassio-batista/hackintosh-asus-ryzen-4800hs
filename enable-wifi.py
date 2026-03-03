import plistlib

CONFIG_PATH = r"U:\EFI\OC\config.plist"

with open(CONFIG_PATH, 'rb') as f:
    config = plistlib.load(f)

for kx in config['Kernel']['Add']:
    name = kx.get('BundlePath', '')
    if 'AirportItlwm' in name:
        kx['Enabled'] = True
        print(f'Habilitando {name} para usar Wi-Fi no Recovery!')

with open(CONFIG_PATH, 'wb') as f:
    plistlib.dump(config, f)
