import plistlib

CONFIG = r'C:\Users\cassi\git\New folder\HackintoshEFI\EFI\OC\config.plist'

with open(CONFIG, 'rb') as f:
    c = plistlib.load(f)

bq = c['Booter']['Quirks']
print("=== ANALISE RAIZ DO PCI HANG ===")
print()
print("Boot 3 (PCI FUNCIONOU, panico depois por VoodooInput):")
print("  DevirtualiseMmio: True")
print("  ProtectUefiServices: True")
print()
print("Boot 5 atual (PCI HANG):")
print(f"  DevirtualiseMmio: {bq['DevirtualiseMmio']}")
print(f"  ProtectUefiServices: {bq['ProtectUefiServices']}")
print()
print("ASUS TUF A15 4800H (confirmado funcionando):")
print("  DevirtualiseMmio: True")
print("  ProtectUefiServices: False")
print()
print("==> CAUSA RAIZ: DevirtualiseMmio=False bloqueia MMIO dos dispositivos PCI!")
print("==> FIX: Setar DevirtualiseMmio=True")
print()

# Aplicar correcao
bq['DevirtualiseMmio'] = True
print(f"[FIX] DevirtualiseMmio: False -> True")

with open(CONFIG, 'wb') as f:
    plistlib.dump(c, f)

print("[OK] Config salvo!")

# Verificar
with open(CONFIG, 'rb') as f:
    v = plistlib.load(f)

print()
print("=== BOOTER QUIRKS FINAIS ===")
for k in sorted(v['Booter']['Quirks'].keys()):
    val = v['Booter']['Quirks'][k]
    print(f"  {k}: {val}")
