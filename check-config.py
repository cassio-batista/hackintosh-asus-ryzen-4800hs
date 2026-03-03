import plistlib

with open(r'C:\Users\cassi\git\New folder\HackintoshEFI\EFI\OC\config.plist', 'rb') as f:
    p = plistlib.load(f)

print("=== BOOTER QUIRKS ===")
for k, v in sorted(p['Booter']['Quirks'].items()):
    print(f"  {k}: {v}")

print("\n=== SMBIOS ===")
pi = p['PlatformInfo']['Generic']
print(f"  SystemProductName: {pi.get('SystemProductName', 'N/A')}")

print("\n=== NVRAM boot-args ===")
ba = p['NVRAM']['Add'].get('7C436110-AB2A-4BBB-A880-FE41995C9F82', {}).get('boot-args', '')
print(f"  {ba}")

print("\n=== Misc Security ===")
sec = p['Misc']['Security']
print(f"  DmgLoading: {sec.get('DmgLoading')}")
print(f"  SecureBootModel: {sec.get('SecureBootModel')}")
print(f"  Vault: {sec.get('Vault')}")

print("\n=== Kernel Emulate ===")
emu = p['Kernel'].get('Emulate', {})
print(f"  DummyPowerManagement: {emu.get('DummyPowerManagement')}")

print("\n=== UEFI Quirks ===")
uq = p['UEFI']['Quirks']
print(f"  ReleaseUsbOwnership: {uq.get('ReleaseUsbOwnership')}")

print("\n=== Disabled Kexts ===")
for kext in p['Kernel']['Add']:
    if not kext.get('Enabled', True):
        print(f"  {kext['BundlePath']}")

print("\n=== Disabled Patches ===")
for i, patch in enumerate(p['Kernel']['Patch']):
    if not patch.get('Enabled', True):
        print(f"  [{i}] {patch.get('Comment', 'N/A')}")
