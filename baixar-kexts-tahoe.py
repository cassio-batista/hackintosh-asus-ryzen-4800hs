#!/usr/bin/env python3
"""
Script: baixar-kexts-tahoe.py
Baixa automaticamente os kexts mais recentes do GitHub para o upgrade Tahoe.
Uso: python baixar-kexts-tahoe.py
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
from pathlib import Path

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError
except ImportError:
    print("ERRO: Python 3 necessario.")
    sys.exit(1)

# Diretório onde os kexts serão extraídos (subpasta desta pasta)
SCRIPT_DIR = Path(__file__).parent
KEXTS_OUT = SCRIPT_DIR / "_tahoe_kexts"
EFI_KEXTS = SCRIPT_DIR / "efi_macos" / "EFI" / "OC" / "Kexts"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/vnd.github.v3+json",
}

# Lista de kexts a baixar: (repositório, nome do arquivo no release, kexts dentro do zip)
KEXTS = [
    {
        "repo": "acidanthera/Lilu",
        "asset_contains": "RELEASE.zip",
        "kexts": ["Lilu.kext"],
        "priority": "CRITICA",
    },
    {
        "repo": "acidanthera/VirtualSMC",
        "asset_contains": "RELEASE.zip",
        "kexts": [
            "VirtualSMC.kext",
            "SMCBatteryManager.kext",
            "SMCLightSensor.kext",
            "SMCProcessorAMD.kext",
        ],
        "priority": "CRITICA",
    },
    {
        "repo": "acidanthera/AppleALC",
        "asset_contains": "RELEASE.zip",
        "kexts": ["AppleALC.kext"],
        "priority": "ALTA",
    },
    {
        "repo": "acidanthera/RestrictEvents",
        "asset_contains": "RELEASE.zip",
        "kexts": ["RestrictEvents.kext"],
        "priority": "ALTA",
    },
    {
        "repo": "acidanthera/NVMeFix",
        "asset_contains": "RELEASE.zip",
        "kexts": ["NVMeFix.kext"],
        "priority": "MEDIA",
    },
    {
        "repo": "acidanthera/BrightnessKeys",
        "asset_contains": "RELEASE.zip",
        "kexts": ["BrightnessKeys.kext"],
        "priority": "BAIXA",
    },
    {
        "repo": "acidanthera/VoodooPS2",
        "asset_contains": "RELEASE.zip",
        "kexts": ["VoodooPS2Controller.kext"],
        "priority": "MEDIA",
    },
    {
        "repo": "ChefKissInc/NootedRed",
        "asset_contains": ".zip",
        "kexts": ["NootedRed.kext"],
        "priority": "CRITICA - BLOQUEADORA",
    },
    {
        "repo": "ChefKissInc/ForgedInvariant",
        "asset_contains": ".zip",
        "kexts": ["ForgedInvariant.kext"],
        "priority": "MEDIA",
    },
    {
        "repo": "OpenIntelWireless/itlwm",
        "asset_contains": "itlwm_v",
        "asset_not_contains": "Airport",
        "kexts": ["itlwm.kext"],
        "priority": "CRITICA",
    },
    {
        "repo": "OpenIntelWireless/IntelBluetoothFirmware",
        "asset_contains": "IntelBluetoothFirmware",
        "kexts": ["IntelBluetoothFirmware.kext", "IntelBTPatcher.kext", "BlueToolFixup.kext"],
        "priority": "ALTA",
    },
    {
        "repo": "1Revenger1/ECEnabler",
        "asset_contains": "RELEASE.zip",
        "kexts": ["ECEnabler.kext"],
        "priority": "BAIXA",
    },
    {
        "repo": "dhinakg/AMFIPass",
        "asset_contains": "RELEASE.zip",
        "kexts": ["AMFIPass.kext"],
        "priority": "ALTA",
    },
    {
        "repo": "VoodooI2C/VoodooI2C",
        "asset_contains": "VoodooI2C-",
        "kexts": ["VoodooI2C.kext", "VoodooI2CHID.kext", "VoodooI2CELAN.kext"],
        "priority": "MEDIA",
    },
    {
        "repo": "AppleIntelWifi/AppleIntelWifiAdapter",
        "asset_contains": "AirportItlwm",
        "kexts": ["AirportItlwm.kext"],
        "priority": "BAIXA - desabilitada no Tahoe",
        "optional": True,
    },
]


def github_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return None


def download_file(url, dest_path):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=60) as r, open(dest_path, "wb") as f:
        while True:
            chunk = r.read(65536)
            if not chunk:
                break
            f.write(chunk)


def find_kexts_in_zip(zip_path, wanted_kexts):
    """Encontra os caminhos dos kexts dentro do zip."""
    found = {}
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            for kext in wanted_kexts:
                # Queremos o diretório raiz .kext e seus conteúdos
                if (name == kext + "/" or name.startswith(kext + "/")) and kext not in found:
                    found[kext] = name.split("/")[0]
    return found


def extract_kext(zip_path, kext_name, dest_dir):
    """Extrai um .kext específico do zip para dest_dir."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        members = [m for m in z.namelist() if m.startswith(kext_name + "/") or m == kext_name]
        if not members:
            # Tenta encontrar em subpastas
            members = [m for m in z.namelist() if ("/" + kext_name + "/") in m or m.endswith("/" + kext_name)]
            if not members:
                return False
            # Ajusta o prefixo
            prefix = members[0].split(kext_name)[0]
            members_strip = [(m, m[len(prefix):]) for m in members if m.startswith(prefix + kext_name)]
        else:
            prefix = ""
            members_strip = [(m, m) for m in members]

        for orig, rel in members_strip:
            rel = rel.lstrip("/")
            if not rel:
                continue
            target = dest_dir / rel
            if orig.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(orig) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    return True


def main():
    print("=" * 60)
    print("  Downloader de Kexts - macOS Tahoe (Ryzentosh Recovery)")
    print("=" * 60)
    print()

    KEXTS_OUT.mkdir(exist_ok=True)

    results = []

    for entry in KEXTS:
        repo = entry["repo"]
        wanted = entry["kexts"]
        priority = entry["priority"]
        optional = entry.get("optional", False)

        print(f"[{priority}] {repo}")
        release = github_latest_release(repo)
        if not release:
            print(f"  ⚠️  Falha ao obter release de {repo}")
            results.append((repo, wanted, "ERRO - sem release"))
            continue

        version = release.get("tag_name", "?")
        assets = release.get("assets", [])

        # Selecionar asset correto
        asset = None
        contains = entry.get("asset_contains", ".zip")
        not_contains = entry.get("asset_not_contains", "")
        for a in assets:
            name = a["name"]
            if contains.lower() in name.lower():
                if not_contains and not_contains.lower() in name.lower():
                    continue
                if name.endswith(".zip"):
                    asset = a
                    break

        if not asset:
            print(f"  ⚠️  Asset não encontrado para {repo} v{version}")
            results.append((repo, wanted, f"ERRO - asset não encontrado (v{version})"))
            continue

        print(f"  → v{version}: {asset['name']}")

        # Download para temp
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            print(f"  ↓ Baixando...", end="", flush=True)
            download_file(asset["browser_download_url"], tmp_path)
            print(" OK")

            # Extrair cada kext
            extracted = []
            missing = []
            for kext_name in wanted:
                dest = KEXTS_OUT / kext_name
                if dest.exists():
                    shutil.rmtree(dest)
                ok = extract_kext(tmp_path, kext_name, KEXTS_OUT)
                if ok and (KEXTS_OUT / kext_name).exists():
                    extracted.append(kext_name)
                    print(f"  ✅ {kext_name}")
                else:
                    missing.append(kext_name)
                    print(f"  ⚠️  {kext_name} não encontrado no zip")

            if extracted:
                results.append((repo, extracted, f"OK v{version}"))
            if missing:
                results.append((repo, missing, f"NÃO ENCONTRADO no zip"))

        except Exception as e:
            print(f"  ❌ Erro: {e}")
            results.append((repo, wanted, f"ERRO: {e}"))
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        print()

    # Sumário
    print("=" * 60)
    print("  SUMÁRIO")
    print("=" * 60)
    ok_count = sum(1 for _, _, s in results if s.startswith("OK"))
    err_count = len(results) - ok_count
    print(f"  Sucesso: {ok_count} | Erros/Avisos: {err_count}")
    print()
    print(f"  Kexts baixados em: {KEXTS_OUT}")
    print()

    # Perguntar se quer copiar para EFI
    if ok_count > 0 and EFI_KEXTS.exists():
        print("Deseja copiar os kexts baixados para a EFI? (efi_macos/EFI/OC/Kexts/)")
        print("ATENÇÃO: Isso substituirá os kexts atuais na EFI!")
        ans = input("Copiar? [s/N]: ").strip().lower()
        if ans == "s":
            copy_to_efi()
    else:
        print("  Para copiar manualmente para a EFI depois:")
        print(f"  python baixar-kexts-tahoe.py --copy")
    print()


def copy_to_efi():
    print()
    print("Copiando kexts para EFI...")
    copied = 0
    skipped = 0
    for kext_dir in KEXTS_OUT.iterdir():
        if kext_dir.suffix == ".kext" and kext_dir.is_dir():
            dest = EFI_KEXTS / kext_dir.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(kext_dir, dest)
            print(f"  ✅ {kext_dir.name}")
            copied += 1
    print(f"\n  {copied} kexts copiados para {EFI_KEXTS}")
    print("  PRÓXIMO PASSO: Copie a pasta efi_macos/EFI/ para o pendrive!")


if __name__ == "__main__":
    if "--copy" in sys.argv:
        copy_to_efi()
    else:
        main()
