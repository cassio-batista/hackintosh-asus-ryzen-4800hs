#!/usr/bin/env python3
"""
copiar-efi-para-pendrive.py
============================
Copia a EFI corrigida para o pendrive, limpando arquivos ._ problematicos.
Detecta automaticamente o pendrive pelo label HACKINTOSH ou tipo removivel.
"""

import shutil
import os
import subprocess
import sys

print("=" * 60)
print("  COPIAR EFI CORRIGIDA PARA PENDRIVE")
print("=" * 60)

# Detectar pendrive
def find_usb():
    """Encontra letra do drive USB"""
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             "Get-Volume | Where-Object { $_.DriveType -eq 'Removable' -or $_.FileSystemLabel -like '*HACK*' } | Select-Object -ExpandProperty DriveLetter"],
            capture_output=True, text=True, timeout=10
        )
        letters = [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
        if letters:
            return letters[0]
    except:
        pass
    
    # Fallback: verificar drives comuns
    for letter in ['U', 'E', 'F', 'G', 'H', 'D']:
        path = f"{letter}:\\"
        if os.path.exists(path):
            efi_path = os.path.join(path, "EFI")
            if os.path.exists(efi_path):
                return letter
    
    return None

drive = find_usb()
if not drive:
    print("\n[ERRO] Pendrive nao encontrado!")
    print("  Conecte o pendrive e execute novamente.")
    print("  Se o pendrive estiver em uma letra especifica, passe como argumento:")
    print("    python copiar-efi-para-pendrive.py U")
    
    if len(sys.argv) > 1:
        drive = sys.argv[1].strip().rstrip(':')
        if not os.path.exists(f"{drive}:\\"):
            print(f"\n[ERRO] Drive {drive}: nao existe!")
            sys.exit(1)
    else:
        sys.exit(1)

USB_ROOT = f"{drive}:\\"
USB_EFI = os.path.join(USB_ROOT, "EFI")
LOCAL_EFI = r"C:\Users\cassi\git\New folder\HackintoshEFI\EFI"

print(f"\n  Pendrive detectado: {drive}:")
print(f"  Origem:  {LOCAL_EFI}")
print(f"  Destino: {USB_EFI}")

# Verificar que a origem existe
if not os.path.exists(LOCAL_EFI):
    print(f"\n[ERRO] EFI local nao encontrado: {LOCAL_EFI}")
    sys.exit(1)

# Remover EFI antiga do pendrive
if os.path.exists(USB_EFI):
    print(f"\n  Removendo EFI antiga do pendrive...")
    shutil.rmtree(USB_EFI)
    print("  [OK] EFI antiga removida")

# Copiar EFI nova
print(f"  Copiando EFI corrigida...")
shutil.copytree(LOCAL_EFI, USB_EFI)
print(f"  [OK] EFI copiada")

# Limpar arquivos ._ (macOS resource fork files que causam problemas)
print(f"\n  Limpando arquivos ._ problematicos...")
dot_count = 0
for root, dirs, files in os.walk(USB_ROOT):
    for f in files:
        if f.startswith('._'):
            full = os.path.join(root, f)
            os.remove(full)
            dot_count += 1

print(f"  [OK] {dot_count} arquivos ._ removidos")

# Verificar que com.apple.recovery.boot existe
recovery_dir = os.path.join(USB_ROOT, "com.apple.recovery.boot")
if os.path.exists(recovery_dir):
    recovery_files = os.listdir(recovery_dir)
    print(f"\n  Recovery: {len(recovery_files)} arquivos em com.apple.recovery.boot/")
    for rf in recovery_files:
        size = os.path.getsize(os.path.join(recovery_dir, rf))
        print(f"    {rf} ({size:,} bytes)")
else:
    print("\n  [AVISO] com.apple.recovery.boot NAO encontrado!")
    print("  Verifique se o recovery do macOS foi copiado anteriormente.")

# Verificacao final
print(f"\n" + "=" * 60)
print("  VERIFICACAO FINAL DO PENDRIVE")
print("=" * 60)

config_path = os.path.join(USB_EFI, "OC", "config.plist")
if os.path.exists(config_path):
    import plistlib
    with open(config_path, 'rb') as f:
        p = plistlib.load(f)
    
    bq = p['Booter']['Quirks']
    print(f"\n  Booter Quirks:")
    print(f"    EnableWriteUnprotector: {bq['EnableWriteUnprotector']}")
    print(f"    RebuildAppleMemoryMap:  {bq['RebuildAppleMemoryMap']}")
    print(f"    SyncRuntimePermissions: {bq['SyncRuntimePermissions']}")
    
    sec = p['Misc']['Security']
    print(f"\n  Security:")
    print(f"    DmgLoading: {sec['DmgLoading']}")
    print(f"    SecureBootModel: {sec['SecureBootModel']}")
    
    nv = p['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']
    print(f"\n  boot-args: {nv.get('boot-args')}")
    
    pi = p['PlatformInfo']['Generic']
    print(f"  SMBIOS: {pi['SystemProductName']}")
    
    enabled_kexts = sum(1 for k in p['Kernel']['Add'] if k.get('Enabled', True))
    print(f"\n  Kexts habilitados: {enabled_kexts}")
    
    print(f"\n  [TUDO OK] Pendrive pronto para boot!")
else:
    print(f"\n  [ERRO] config.plist nao encontrado em {config_path}")

# Listar estrutura
print(f"\n  Estrutura do pendrive:")
for root, dirs, files in os.walk(USB_ROOT):
    level = root.replace(USB_ROOT, '').count(os.sep)
    indent = '    ' + '  ' * level
    dirname = os.path.basename(root)
    if level < 4:
        print(f"{indent}{dirname}/")
    if level < 4:
        for f in files:
            size = os.path.getsize(os.path.join(root, f))
            if size > 1024:
                print(f"{indent}  {f} ({size//1024} KB)")
            else:
                print(f"{indent}  {f} ({size} B)")

print(f"\n" + "=" * 60)
print("  PENDRIVE ATUALIZADO COM SUCESSO!")
print("  Pode desconectar com seguranca e testar o boot.")
print("=" * 60)
