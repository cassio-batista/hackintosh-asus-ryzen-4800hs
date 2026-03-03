import plistlib

config_path = r'U:\EFI\OC\config.plist'
with open(config_path, 'rb') as f:
    config = plistlib.load(f)

# Remove RealtekRTL8111 entry from Kernel > Add
original = len(config['Kernel']['Add'])
config['Kernel']['Add'] = [k for k in config['Kernel']['Add'] if 'RealtekRTL8111' not in k.get('BundlePath', '')]
removed = original - len(config['Kernel']['Add'])
new_count = len(config['Kernel']['Add'])
print('Removed', removed, 'Realtek entries, now', new_count, 'kexts')

# Verify AppleMCEReporterDisabler entry
for k in config['Kernel']['Add']:
    bp = k.get('BundlePath', '')
    if 'AppleMCEReporter' in bp:
        print('AppleMCEReporterDisabler:', bp, 'PlistPath:', k['PlistPath'], 'Enabled:', k['Enabled'])

with open(config_path, 'wb') as f:
    plistlib.dump(config, f, sort_keys=False)
print('config.plist atualizado!')
