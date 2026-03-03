#!/usr/bin/env python3
"""Analyze TUF A15 reference config vs our config"""
import plistlib
import json
import sys

ref_path = r'C:\Users\cassi\git\New folder\tuf-a15-ref\HACKINTOSH-EFI-ASUS-TUF-A15-RYZEN-7-4800H-main\EFI\OC\config.plist'
our_path = r'U:\EFI\OC\config.plist'

with open(ref_path, 'rb') as f:
    ref = plistlib.load(f)
with open(our_path, 'rb') as f:
    our = plistlib.load(f)

print("=" * 60)
print("COMPARACAO: TUF A15 REFERENCE vs NOSSO CONFIG")
print("=" * 60)

# ACPI
print("\n--- ACPI ADD ---")
print("REF:")
for a in ref['ACPI']['Add']:
    print(f"  {a['Path']} En={a['Enabled']}")
print("NOSSO:")
for a in our['ACPI']['Add']:
    print(f"  {a['Path']} En={a['Enabled']}")

# ACPI Patches
print("\n--- ACPI PATCHES ---")
ref_patches = ref['ACPI'].get('Patch', [])
our_patches = our['ACPI'].get('Patch', [])
print(f"REF: {len(ref_patches)} patches")
for p in ref_patches:
    print(f"  {p.get('Comment','')} En={p['Enabled']}")
print(f"NOSSO: {len(our_patches)} patches")
for p in our_patches:
    print(f"  {p.get('Comment','')} En={p['Enabled']}")

# Booter Quirks
print("\n--- BOOTER QUIRKS (diff only) ---")
for k in set(list(ref['Booter']['Quirks'].keys()) + list(our['Booter']['Quirks'].keys())):
    rv = ref['Booter']['Quirks'].get(k)
    ov = our['Booter']['Quirks'].get(k)
    if rv != ov:
        print(f"  {k}: REF={rv} OURS={ov}")

# Kernel Add (kexts)
print("\n--- KEXTS REF ---")
for i, k in enumerate(ref['Kernel']['Add']):
    print(f"  {i}: {k['BundlePath']} En={k['Enabled']}")

print("\n--- KEXTS NOSSO ---")
for i, k in enumerate(our['Kernel']['Add']):
    print(f"  {i}: {k['BundlePath']} En={k['Enabled']}")

# Kernel Block
print("\n--- KERNEL BLOCK ---")
print("REF:")
for b in ref['Kernel'].get('Block', []):
    print(f"  {b['Identifier']} En={b['Enabled']}")
print("NOSSO:")
for b in our['Kernel'].get('Block', []):
    print(f"  {b['Identifier']} En={b['Enabled']}")

# Kernel Emulate
print("\n--- KERNEL EMULATE ---")
print(f"REF DummyPowerManagement: {ref['Kernel']['Emulate'].get('DummyPowerManagement')}")
print(f"OURS DummyPowerManagement: {our['Kernel']['Emulate'].get('DummyPowerManagement')}")

# Kernel Quirks
print("\n--- KERNEL QUIRKS (diff only) ---")
for k in set(list(ref['Kernel']['Quirks'].keys()) + list(our['Kernel']['Quirks'].keys())):
    rv = ref['Kernel']['Quirks'].get(k)
    ov = our['Kernel']['Quirks'].get(k)
    if rv != ov:
        print(f"  {k}: REF={rv} OURS={ov}")

# Kernel Patches count
print("\n--- KERNEL PATCHES ---")
ref_kp = ref['Kernel'].get('Patch', [])
our_kp = our['Kernel'].get('Patch', [])
ref_en = [p for p in ref_kp if p.get('Enabled')]
our_en = [p for p in our_kp if p.get('Enabled')]
print(f"REF: {len(ref_kp)} total, {len(ref_en)} enabled")
print(f"OURS: {len(our_kp)} total, {len(our_en)} enabled")

# NVRAM
print("\n--- NVRAM ---")
guid = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
ref_nv = ref['NVRAM']['Add'].get(guid, {})
our_nv = our['NVRAM']['Add'].get(guid, {})
print(f"REF boot-args: {ref_nv.get('boot-args','')}")
print(f"OUR boot-args: {our_nv.get('boot-args','')}")
ref_csr = ref_nv.get('csr-active-config', b'')
our_csr = our_nv.get('csr-active-config', b'')
print(f"REF csr: {ref_csr.hex() if isinstance(ref_csr, bytes) else ref_csr}")
print(f"OUR csr: {our_csr.hex() if isinstance(our_csr, bytes) else our_csr}")

# PlatformInfo
print("\n--- PLATFORMINFO ---")
ref_gen = ref.get('PlatformInfo', {}).get('Generic', {})
our_gen = our.get('PlatformInfo', {}).get('Generic', {})
print(f"REF SMBIOS: {ref_gen.get('SystemProductName','')}")
print(f"OUR SMBIOS: {our_gen.get('SystemProductName','')}")

# UEFI Drivers
print("\n--- UEFI DRIVERS ---")
print("REF:")
for d in ref['UEFI']['Drivers']:
    if isinstance(d, str):
        print(f"  {d}")
    else:
        print(f"  {d.get('Path','')} LoadEarly={d.get('LoadEarly',False)}")
print("NOSSO:")
for d in our['UEFI']['Drivers']:
    if isinstance(d, str):
        print(f"  {d}")
    else:
        print(f"  {d.get('Path','')} LoadEarly={d.get('LoadEarly',False)}")

# Misc Security
print("\n--- MISC SECURITY ---")
ref_sec = ref['Misc']['Security']
our_sec = our['Misc']['Security']
for k in ['DmgLoading', 'SecureBootModel', 'Vault']:
    print(f"  {k}: REF={ref_sec.get(k,'')} OURS={our_sec.get(k,'')}")

# UEFI Quirks diff
print("\n--- UEFI QUIRKS (diff only) ---")
for k in set(list(ref['UEFI']['Quirks'].keys()) + list(our['UEFI']['Quirks'].keys())):
    rv = ref['UEFI']['Quirks'].get(k)
    ov = our['UEFI']['Quirks'].get(k)
    if rv != ov:
        print(f"  {k}: REF={rv} OURS={ov}")
