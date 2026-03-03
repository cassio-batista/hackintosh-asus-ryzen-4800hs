import plistlib

with open(r'U:\EFI\OC\config.plist', 'rb') as f:
    c = plistlib.load(f)

print('=== BOOTER QUIRKS ===')
bq = c['Booter']['Quirks']
for k in sorted(bq.keys()):
    print('  %s: %s' % (k, bq[k]))

print()
print('=== KERNEL EMULATE ===')
ke = c['Kernel']['Emulate']
for k in sorted(ke.keys()):
    print('  %s: %s' % (k, ke[k]))

print()
print('=== KERNEL QUIRKS ===')
kq = c['Kernel']['Quirks']
for k in sorted(kq.keys()):
    print('  %s: %s' % (k, kq[k]))

print()
print('=== MISC SECURITY ===')
ms = c['Misc']['Security']
for k in sorted(ms.keys()):
    print('  %s: %s' % (k, ms[k]))

print()
print('=== NVRAM ===')
nv = c['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']
print('  boot-args: %s' % nv.get('boot-args', ''))
csr = nv.get('csr-active-config', b'')
print('  csr-active-config: %s' % csr.hex())

print()
print('=== PLATFORM INFO ===')
pi = c['PlatformInfo']['Generic']
print('  SystemProductName: %s' % pi['SystemProductName'])

print()
print('=== KEXTS (order) ===')
for i, k in enumerate(c['Kernel']['Add']):
    exe = k.get('ExecutablePath', '')
    en = k.get('Enabled', True)
    status = 'ON' if en else 'OFF'
    bp = k['BundlePath']
    print('  %2d. [%s] %-45s Exe=%s' % (i, status, bp, exe))

print()
print('=== PATCHES ===')
for i, p in enumerate(c['Kernel']['Patch']):
    en = p.get('Enabled', False)
    comment = p.get('Comment', '')
    mk = p.get('MinKernel', '')
    xk = p.get('MaxKernel', '')
    base = p.get('Base', '')
    status = 'ON' if en else 'OFF'
    print('  %2d. [%s] %-60s Min=%-10s Max=%-10s Base=%s' % (i, status, comment[:60], mk, xk, base))
    if 'cpuid_cores_per_package' in comment.lower():
        repl_hex = p.get('Replace', b'').hex()
        find_hex = p.get('Find', b'').hex()
        mask_hex = p.get('Mask', b'').hex() if p.get('Mask') else 'none'
        rmask_hex = p.get('ReplaceMask', b'').hex() if p.get('ReplaceMask') else 'none'
        print('      Find: %s  Mask: %s' % (find_hex, mask_hex))
        print('      Replace: %s  ReplaceMask: %s' % (repl_hex, rmask_hex))

print()
print('=== ACPI ===')
for a in c['ACPI']['Add']:
    status = 'ON' if a.get('Enabled', True) else 'OFF'
    print('  [%s] %s' % (status, a['Path']))

print()
print('=== DRIVERS ===')
for d in c['UEFI']['Drivers']:
    status = 'ON' if d.get('Enabled', True) else 'OFF'
    print('  [%s] %s' % (status, d['Path']))

print()
print('=== UEFI QUIRKS ===')
uq = c['UEFI']['Quirks']
for k in sorted(uq.keys()):
    print('  %s: %s' % (k, uq[k]))

print()
print('=== DeviceProperties ===')
dp = c.get('DeviceProperties', {}).get('Add', {})
for path, props in dp.items():
    print('  %s:' % path)
    for pk, pv in props.items():
        print('    %s = %s' % (pk, pv))
