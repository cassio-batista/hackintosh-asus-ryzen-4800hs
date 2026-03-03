import os
import shutil
import sys
import time

sys.stdout.write("Procurando o pendrive... ")
usb_drive = None
# Acha o pendrive
for letter in 'DEFGHIJKLMNOPQRSTUVWXYZ':
    if os.path.exists(f'{letter}:\\EFI'):
        usb_drive = f'{letter}:'
        break

if not usb_drive:
    print("NÃO ENCONTRADO! Conecte seu pendrive com a pasta EFI na raiz e tente novamente.")
    sys.exit(1)

print(f"ENCONTRADO na letra {usb_drive}!")

print(f"\n>> Copiando EFI de 'efi_macos\\EFI' para {usb_drive}\\EFI...")
if os.path.exists(f'{usb_drive}\\EFI'):
    shutil.rmtree(f'{usb_drive}\\EFI')
shutil.copytree('efi_macos\\EFI', f'{usb_drive}\\EFI')

print(f"\n>> Copiando aplicativo HeliPort.dmg para a raiz do pendrive...")
if os.path.exists('HeliPort.dmg'):
    shutil.copy2('HeliPort.dmg', f'{usb_drive}\\HeliPort.dmg')
    print("  -> HeliPort.dmg copiado com sucesso!")
else:
    print("  -> HeliPort.dmg não encontrado na pasta atual. Baixando de novo...")
    import urllib.request
    urllib.request.urlretrieve('https://github.com/OpenIntelWireless/HeliPort/releases/download/v1.5.0/HeliPort.dmg', f'{usb_drive}\\HeliPort.dmg')
    print("  -> HeliPort.dmg baixado 100%!")

print("\nTUDO PRONTO! O Pendrive está preparado com a correção final de Touchpad (I2C) e o aplicativo do Wi-Fi.")
print("  => Ejete, coloque no Mac, limpe o NVRAM e dê boot!")