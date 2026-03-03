import os
import urllib.request
import json
import zipfile
import plistlib
import shutil

# Configurações da rede Wi-Fi e drive
WIFI_SSID = "SEU_SSID_AQUI"
WIFI_PWD = "SUA_SENHA_AQUI"
USB_DRIVE = "U:\\"

def main():
    print("Buscando a última versão estável do itlwm no GitHub...")
    req = urllib.request.Request("https://api.github.com/repos/OpenIntelWireless/itlwm/releases/latest")
    
    try:
        response = urllib.request.urlopen(req)
        release_data = json.loads(response.read())
    except Exception as e:
        print(f"Erro ao buscar a release: {e}")
        return

    asset_url = None
    for asset in release_data.get("assets", []):
        name = asset["name"]
        # Filtrar pelo itlwm apenas (e não AirportItlwm)
        if name.startswith("itlwm_") and name.endswith(".zip"):
            asset_url = asset["browser_download_url"]
            print(f"Versão encontrada: {name}")
            break

    if not asset_url:
        print("Erro: Não foi possível encontrar a URL de download do itlwm.")
        return

    zip_path = "itlwm_download.zip"
    print(f"Baixando de: {asset_url}...")
    urllib.request.urlretrieve(asset_url, zip_path)

    extract_dir = "itlwm_extracted"
    print("Extraindo o arquivo kext...")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
        
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    # Localizar a kext propriamente dita após a extração
    kext_src_path = None
    for root, dirs, files in os.walk(extract_dir):
        if "itlwm.kext" in dirs:
            kext_src_path = os.path.join(root, "itlwm.kext")
            break

    if not kext_src_path:
        print("Erro: Diretório itlwm.kext não encontrado nos arquivos extraídos.")
        return

    print("Injetando configurações de Wi-Fi no Info.plist...")
    info_plist_path = os.path.join(kext_src_path, "Contents", "Info.plist")
    
    with open(info_plist_path, "rb") as f:
        kext_plist = plistlib.load(f)

    # Aplicando o SSID e Senha dentro de IOKitPersonalities -> itlwm -> WiFiConfig
    try:
        wifi_config = kext_plist["IOKitPersonalities"]["itlwm"]["WiFiConfig"]
        wifi_config["WiFi_1"] = {
            "ssid": WIFI_SSID,
            "pwd": WIFI_PWD
        }
        with open(info_plist_path, "wb") as f:
            plistlib.dump(kext_plist, f)
        print(f"Credenciais para o SSID '{WIFI_SSID}' salvas no Info.plist com sucesso!")
    except KeyError:
        print("Aviso: A chave IOKitPersonalities->itlwm->WiFiConfig não foi encontrada no Info.plist.")

    # Copiando para U:\
    print(f"Copiando a kext modificada para {USB_DRIVE}EFI\\OC\\Kexts...")
    kext_dest_path = os.path.join(USB_DRIVE, "EFI", "OC", "Kexts", "itlwm.kext")
    
    # Cria o diretório se por algum motivo ainda não existir
    os.makedirs(os.path.dirname(kext_dest_path), exist_ok=True)
    
    if os.path.exists(kext_dest_path):
        shutil.rmtree(kext_dest_path)
    shutil.copytree(kext_src_path, kext_dest_path)

    print(f"Atualizando {USB_DRIVE}EFI\\OC\\config.plist...")
    config_path = os.path.join(USB_DRIVE, "EFI", "OC", "config.plist")
    
    if not os.path.exists(config_path):
        print(f"Erro: config.plist não encontrado no caminho {config_path}.")
    else:
        with open(config_path, "rb") as f:
            config = plistlib.load(f)

        itlwm_found = False
        
        # Desliga AirportItlwm e liga itlwm
        for kext in config["Kernel"]["Add"]:
            if kext["BundlePath"].startswith("AirportItlwm"):
                kext["Enabled"] = False
                print(f"Desabilitado: {kext['BundlePath']}")
            elif kext["BundlePath"] == "itlwm.kext":
                kext["Enabled"] = True
                itlwm_found = True
                print("Habilitado: itlwm.kext")

        # Se o itlwm não existia no config, injeta a entrada dele
        if not itlwm_found:
            print("Adicionando nova entrada para o itlwm.kext no config.plist...")
            config["Kernel"]["Add"].append({
                "Arch": "x86_64",
                "BundlePath": "itlwm.kext",
                "Comment": "Intel Wi-Fi (itlwm)",
                "Enabled": True,
                "ExecutablePath": "Contents/MacOS/itlwm",
                "MaxKernel": "",
                "MinKernel": "",
                "PlistPath": "Contents/Info.plist"
            })

        with open(config_path, "wb") as f:
            plistlib.dump(config, f)
        
        print("config.plist atualizado com sucesso.")

    # Limpeza
    print("Limpando arquivos temporários...")
    try:
        os.remove(zip_path)
        shutil.rmtree(extract_dir)
    except Exception:
        pass

    print("Processo concluído! Verifique a unidade U: e proceda com o boot.")

if __name__ == "__main__":
    main()
