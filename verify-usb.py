import plistlib

with open(r'U:\EFI\OC\config.plist', 'rb') as f:
    c = plistlib.load(f)

bq = c['Booter']['Quirks']
print("=== VERIFICACAO FINAL PENDRIVE U: ===")
print(f"  DevirtualiseMmio:       {bq['DevirtualiseMmio']}")
print(f"  AvoidRuntimeDefrag:     {bq['AvoidRuntimeDefrag']}")
print(f"  EnableWriteUnprotector: {bq['EnableWriteUnprotector']}")
print(f"  RebuildAppleMemoryMap:  {bq['RebuildAppleMemoryMap']}")
print(f"  SyncRuntimePermissions: {bq['SyncRuntimePermissions']}")
print(f"  SetupVirtualMap:        {bq['SetupVirtualMap']}")

print("\n  UEFI Drivers:")
for i, d in enumerate(c['UEFI']['Drivers']):
    le = "LoadEarly" if d.get('LoadEarly', False) else "Normal"
    print(f"    {i+1}. {d['Path']} ({le})")

nv = c['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']
print(f"\n  boot-args: {nv['boot-args']}")

blocks = c['Kernel'].get('Block', [])
print(f"\n  Kernel Block: {len(blocks)} entradas")
for b in blocks:
    print(f"    [{b.get('Enabled','?')}] {b['Identifier']}")

print(f"\n  SMBIOS: {c['PlatformInfo']['Generic']['SystemProductName']}")
print(f"  DmgLoading: {c['Misc']['Security']['DmgLoading']}")
print(f"  SecureBootModel: {c['Misc']['Security']['SecureBootModel']}")

en = sum(1 for k in c['Kernel']['Add'] if k.get('Enabled', True))
dis = sum(1 for k in c['Kernel']['Add'] if not k.get('Enabled', True))
print(f"\n  Kexts: {en} ON, {dis} OFF")
print(f"  Patches: {sum(1 for p in c['Kernel']['Patch'] if p.get('Enabled',True))} ON, {sum(1 for p in c['Kernel']['Patch'] if not p.get('Enabled',True))} OFF")

print("\n  [OK] PENDRIVE PRONTO PARA BOOT!")
