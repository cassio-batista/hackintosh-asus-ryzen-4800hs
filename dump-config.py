import plistlib

with open(r'U:\EFI\OC\config.plist', 'rb') as f:
    c = plistlib.load(f)

print('=== BOOTER QUIRKS ===')
for k,v in sorted(c['Booter']['Quirks'].items()):
    print(f'  {k} = {v}')

print('\n=== KERNEL QUIRKS ===')
for k,v in sorted(c['Kernel']['Quirks'].items()):
    print(f'  {k} = {v}')

print('\n=== KEXTS (Kernel->Add) ===')
for i, kx in enumerate(c['Kernel']['Add']):
    bp = kx['BundlePath']
    en = kx['Enabled']
    print(f'  [{i}] {bp}  => Enabled={en}')

print('\n=== KERNEL PATCHES ===')
for i, p in enumerate(c['Kernel']['Patch']):
    comment = p.get('Comment', '')
    enabled = p['Enabled']
    arch = p.get('Arch', '')
    print(f'  [{i}] {comment} Enabled={enabled} Arch={arch}')
    find_hex = p.get('Find', b'').hex()
    replace_hex = p.get('Replace', b'').hex()
    print(f'       Find={find_hex}  Replace={replace_hex}')

print('\n=== BOOT-ARGS ===')
nvg = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
print(f'  {c["NVRAM"]["Add"][nvg].get("boot-args", "")}')

print('\n=== SMBIOS ===')
print(f'  SystemProductName = {c["PlatformInfo"]["Generic"]["SystemProductName"]}')

print('\n=== ACPI Add ===')
for a in c.get('ACPI', {}).get('Add', []):
    print(f'  {a["Path"]}  Enabled={a["Enabled"]}')

print('\n=== ACPI Patches ===')
for a in c.get('ACPI', {}).get('Patch', []):
    print(f'  {a.get("Comment", "")} Enabled={a["Enabled"]}')

print('\n=== UEFI DRIVERS ===')
for d in c.get('UEFI', {}).get('Drivers', []):
    if isinstance(d, dict):
        print(f'  {d.get("Path", "")} Enabled={d.get("Enabled", True)}')
    else:
        print(f'  {d}')

print('\n=== MISC SECURITY ===')
sec = c['Misc']['Security']
print(f'  SecureBootModel = {sec["SecureBootModel"]}')
print(f'  Vault = {sec["Vault"]}')
print(f'  ScanPolicy = {sec["ScanPolicy"]}')
print(f'  AllowNvramReset = {sec.get("AllowNvramReset", "N/A")}')
print(f'  AllowSetDefault = {sec.get("AllowSetDefault", "N/A")}')

print('\n=== MISC DEBUG ===')
dbg = c['Misc']['Debug']
print(f'  Target = {dbg["Target"]}')
print(f'  DisplayLevel = {dbg["DisplayLevel"]}')
print(f'  AppleDebug = {dbg.get("AppleDebug", "N/A")}')
print(f'  ApplePanic = {dbg.get("ApplePanic", "N/A")}')
