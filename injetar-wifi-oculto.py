import os
import sys
import zipfile
import shutil
import plistlib
import urllib.request
import json

# ==========================================
# PREENCHA COM O NOME DA SUA REDE E SENHA
# ==========================================
WIFI_SSID = "SEU_SSID_AQUI"
WIFI_PWD  = "SUA_SENHA_AQUI"
# ==========================================

OC_KEXTS_DIR = r"U:\EFI\OC\Kexts"
CONFIG_PATH = r"U:\EFI\OC\config.plist"

print("1. Buscando a ultima versao do itlwm.kext...")
try:
    req = urllib.request.Request("https://api.github.com/repos/OpenIntelWireless/itlwm/releases/latest")
    with urllib.request.urlopen(req) as response:
         data = json.loads(response.read().decode())
         
    download_url = None
    for asset in data.get('assets', []):
        name = asset.get('name', '')
        # We want the base itlwm, NOT AirportItlwm
        if name.startswith('itlwm_') and name.endswith('.zip') and 'Airport' not in name:
            download_url = asset['browser_download_url']
            break
            
    if not download_url:
        print("Erro: Link do itlwm.kext não encontrado!")
        sys.exit(1)
        
    print(f"2. Fazendo download do itlwm: {download_url}")
    zip_path = "itlwm_temp.zip"
    urllib.request.urlretrieve(download_url, zip_path)
    
    print("3. Extraindo...")
    extract_dir = "itlwm_temp_ext"
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        
    kext_src = os.path.join(extract_dir, "itlwm.kext")
    if not os.path.exists(kext_src):
        # find it
        for root, dirs, files in os.walk(extract_dir):
            if "itlwm.kext" in dirs:
                kext_src = os.path.join(root, "itlwm.kext")
                break

    print("4. Embutindo sua senha do Wi-Fi direto no driver (Hardcode)...")
    info_plist_path = os.path.join(kext_src, "Contents", "Info.plist")
    with open(info_plist_path, 'rb') as f:
        kext_plist = plistlib.load(f)
        
    # Inject WiFi credentials
    # itlwm looks for IOKitPersonalities -> itlwm -> WiFiConfig
    try:
        wifi_dict = kext_plist['IOKitPersonalities']['itlwm']['WiFiConfig']
        wifi_dict['WiFi_1'] = {
            'password': WIFI_PWD,
            'ssid': WIFI_SSID
        }
    except KeyError:
        print("Aviso: Estrutura WiFiConfig não encontrada, forçando criação...")
        if 'IOKitPersonalities' in kext_plist and 'itlwm' in kext_plist['IOKitPersonalities']:
            kext_plist['IOKitPersonalities']['itlwm']['WiFiConfig'] = {
                'WiFi_1': {
                    'password': WIFI_PWD,
                    'ssid': WIFI_SSID
                }
            }
            
    with open(info_plist_path, 'wb') as f:
        plistlib.dump(kext_plist, f)
        
    print(f"5. Copiando para {OC_KEXTS_DIR}...")
    kext_dest = os.path.join(OC_KEXTS_DIR, "itlwm.kext")
    if os.path.exists(kext_dest):
        shutil.rmtree(kext_dest)
    shutil.copytree(kext_src, kext_dest)
    
    print("6. Atualizando config.plist...")
    with open(CONFIG_PATH, 'rb') as f:
         config = plistlib.load(f)
         
    # Disable AirportItlwm
    for kx in config['Kernel']['Add']:
        if 'AirportItlwm' in kx['BundlePath']:
            kx['Enabled'] = False
            
    # Enable or Add itlwm
    itlwm_found = False
    for kx in config['Kernel']['Add']:
        if kx['BundlePath'] == 'itlwm.kext':
            kx['Enabled'] = True
            itlwm_found = True
            break
            
    if not itlwm_found:
        new_entry = {
            'Arch': 'x86_64',
            'BundlePath': 'itlwm.kext',
            'Comment': 'Intel Wi-Fi (No UI, auto-connect)',
            'Enabled': True,
            'ExecutablePath': 'Contents/MacOS/itlwm',
            'MaxKernel': '',
            'MinKernel': '',
            'PlistPath': 'Contents/Info.plist'
        }
        config['Kernel']['Add'].append(new_entry)
        
    with open(CONFIG_PATH, 'wb') as f:
         plistlib.dump(config, f)
         
    # Cleanup
    os.remove(zip_path)
    shutil.rmtree(extract_dir)
    
    print("="*50)
    print(" SUCESSO! O Pendrive está pronto.")
    print(f" Ele vai se conectar automaticamente e de forma invisivel na rede: {WIFI_SSID}")
    print(" Pode dar o boot novamente.")
    print("="*50)

except Exception as e:
    print(f"Erro: {str(e)}")
