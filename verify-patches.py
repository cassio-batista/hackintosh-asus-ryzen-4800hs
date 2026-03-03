import plistlib

with open(r'C:\Users\cassi\git\New folder\HackintoshEFI\EFI\OC\config.plist', 'rb') as f:
    c = plistlib.load(f)

print("=== PATCHES COM probeBusGated ===")
for i, p in enumerate(c['Kernel']['Patch']):
    if 'probeBusGated' in p.get('Comment','') or 'probeBusGated' in p.get('Base',''):
        print(f"  [{i}] Enabled={p['Enabled']} | {p['Comment']}")

print("\n=== PATCHES COM Visual/time ===")
for i, p in enumerate(c['Kernel']['Patch']):
    if 'Visual' in p.get('Comment','') or 'non-monotonic' in p.get('Comment',''):
        print(f"  [{i}] Enabled={p['Enabled']} | {p['Comment']}")

print(f"\nTotal patches: {len(c['Kernel']['Patch'])}")
print(f"Enabled: {sum(1 for p in c['Kernel']['Patch'] if p.get('Enabled',True))}")
print(f"Disabled: {sum(1 for p in c['Kernel']['Patch'] if not p.get('Enabled',True))}")

print("\n=== TODOS OS PATCHES ===")
for i, p in enumerate(c['Kernel']['Patch']):
    en = "ON " if p.get('Enabled', True) else "OFF"
    print(f"  [{i:2d}] [{en}] {p.get('Comment','N/A')}")
