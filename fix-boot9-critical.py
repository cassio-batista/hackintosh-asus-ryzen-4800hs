#!/usr/bin/env python3
"""
FIX BOOT 9 - Correção Crítica baseada em análise profunda
==========================================================

DIAGNÓSTICO:
1. Boot 8 reiniciou instantaneamente porque:
   - AvoidRuntimeDefrag=False (firmware PRECISA de defrag)
   - EnableWriteUnprotector=True + RebuildAppleMemoryMap=True (CONFLITAM!)
   
2. Boot 7 travava após EXITBS:START porque:
   - AMDRyzenCPUPowerManagement/SMCAMDProcessor podem causar kernel panic
   - Possível falta de SSDT-PLUG-ALT para gerenciamento de CPU
   - AirportItlwm tentava carregar (já desabilitado)

CORREÇÕES:
[CRÍTICO] Reverter AvoidRuntimeDefrag = True (padrão Dortania para TODOS systems)
[CRÍTICO] Reverter EnableWriteUnprotector = False (modo MAT - Dortania AMD Zen)
[SEGURANÇA] Desabilitar AMDRyzenCPUPowerManagement (documentado como instável)
[SEGURANÇA] Desabilitar SMCAMDProcessor (documentado como instável)
[MELHORIA] Adicionar ipc_control_port_options=0 (fix Sonoma)
[MANTER] Todos os SSDTs novos (PLUG-ALT, HPET, XOSI)
[MANTER] AMFIPass, DisableRtcChecksum, ReleaseUsbOwnership=False

REFERÊNCIAS:
- Dortania AMD Zen: EnableWriteUnprotector=NO, RebuildAppleMemoryMap=YES
- mikigal/ryzen-hackintosh: "disable AMDRyzenCPUPowerManagement and SMCAMDProcessor - may cause kernel panic"
- ChefKiss NootedRed: SMBIOS MacBookPro16,2 recomendado (pós-install)
"""

import plistlib
import sys
import shutil
from datetime import datetime

CONFIG_PATH = r"U:\EFI\OC\config.plist"
BACKUP_PATH = r"U:\EFI\OC\config.plist.bak.boot9"

def main():
    print("=" * 70)
    print("FIX BOOT 9 - Correção Crítica")
    print("=" * 70)
    
    # Backup
    shutil.copy2(CONFIG_PATH, BACKUP_PATH)
    print(f"\n[BACKUP] {BACKUP_PATH}")
    
    # Load config
    with open(CONFIG_PATH, 'rb') as f:
        config = plistlib.load(f)
    
    changes = []
    
    # ===================================================================
    # 1. CRÍTICO: Reverter Booter Quirks para modo MAT-compatível
    # ===================================================================
    booter = config['Booter']['Quirks']
    
    # AvoidRuntimeDefrag DEVE ser True para a maioria dos firmwares
    # Dortania não lista como False para NENHUM AMD Zen
    old = booter.get('AvoidRuntimeDefrag', True)
    booter['AvoidRuntimeDefrag'] = True
    changes.append(f"[CRÍTICO] AvoidRuntimeDefrag: {old} -> True (padrão Dortania)")
    
    # EnableWriteUnprotector DEVE ser False com RebuildAppleMemoryMap=True
    # São MUTUAMENTE EXCLUSIVOS per Dortania
    old = booter.get('EnableWriteUnprotector', False)
    booter['EnableWriteUnprotector'] = False
    changes.append(f"[CRÍTICO] EnableWriteUnprotector: {old} -> False (conflita com RebuildAppleMemoryMap)")
    
    # Confirmar que RebuildAppleMemoryMap e SyncRuntimePermissions estão True
    booter['RebuildAppleMemoryMap'] = True
    booter['SyncRuntimePermissions'] = True
    changes.append(f"[CONFIRMAR] RebuildAppleMemoryMap=True, SyncRuntimePermissions=True")
    
    # DevirtualiseMmio - manter True (resolveu PCI hang no boot 5)
    booter['DevirtualiseMmio'] = True
    changes.append(f"[MANTER] DevirtualiseMmio=True (necessário para PCI)")
    
    # SetupVirtualMap - True para nosso hardware (não é B550/A520/X570)
    booter['SetupVirtualMap'] = True
    changes.append(f"[MANTER] SetupVirtualMap=True")
    
    # ProvideCustomSlide - True
    booter['ProvideCustomSlide'] = True
    
    print("\n--- BOOTER QUIRKS ---")
    for c in changes:
        print(f"  {c}")
    
    # ===================================================================
    # 2. SEGURANÇA: Desabilitar kexts problemáticos para instalação
    # ===================================================================
    print("\n--- KERNEL KEXTS ---")
    kext_changes = []
    
    for kext in config['Kernel']['Add']:
        bundle = kext.get('BundlePath', '')
        enabled = kext.get('Enabled', True)
        
        # AMDRyzenCPUPowerManagement - documentado como instável
        if 'AMDRyzenCPUPowerManagement' in bundle and enabled:
            kext['Enabled'] = False
            kext_changes.append(f"[SEGURANÇA] DESABILITADO {bundle} (causa kernel panics em algumas configs)")
        
        # SMCAMDProcessor - documentado como instável
        if 'SMCAMDProcessor' in bundle and enabled:
            kext['Enabled'] = False
            kext_changes.append(f"[SEGURANÇA] DESABILITADO {bundle} (causa freezes/kernel panics)")
        
        # SMCProcessorAMD - já deve estar desabilitado
        if 'SMCProcessorAMD' in bundle and enabled:
            kext['Enabled'] = False
            kext_changes.append(f"[SEGURANÇA] DESABILITADO {bundle}")
    
    for c in kext_changes:
        print(f"  {c}")
    
    # ===================================================================
    # 3. BOOT-ARGS: Adicionar fixes para Sonoma
    # ===================================================================
    print("\n--- BOOT-ARGS ---")
    nvram_guid = '7C436110-AB2A-4BBB-A880-FE41995C9F82'
    nvram = config['NVRAM']['Add'][nvram_guid]
    
    current_args = nvram.get('boot-args', '')
    print(f"  Antes: {current_args}")
    
    new_args = current_args
    
    # Adicionar ipc_control_port_options=0 se não existir (fix Sonoma)
    if 'ipc_control_port_options=0' not in new_args:
        new_args += ' ipc_control_port_options=0'
    
    # Adicionar msgbuf para debug expandido se não existir
    if 'msgbuf=' not in new_args:
        new_args += ' msgbuf=1048576'
    
    # Garantir que não tem espaços duplos
    new_args = ' '.join(new_args.split())
    
    nvram['boot-args'] = new_args
    print(f"  Depois: {new_args}")
    
    # ===================================================================
    # 4. Garantir que NVRAM Delete tem os boot-args para resetar
    # ===================================================================
    nvram_delete = config['NVRAM'].get('Delete', {})
    if nvram_guid not in nvram_delete:
        nvram_delete[nvram_guid] = []
    delete_list = nvram_delete[nvram_guid]
    for key in ['boot-args', 'csr-active-config']:
        if key not in delete_list:
            delete_list.append(key)
    config['NVRAM']['Delete'] = nvram_delete
    print(f"\n  [NVRAM Delete] Garantido reset de boot-args e csr-active-config")
    
    # ===================================================================
    # 5. Verificar Kernel Quirks essenciais
    # ===================================================================
    print("\n--- KERNEL QUIRKS ---")
    kq = config['Kernel']['Quirks']
    
    # PanicNoKextDump - mostrar info em panic
    kq['PanicNoKextDump'] = True
    # PowerTimeoutKernelPanic - prevenir panic em timeout
    kq['PowerTimeoutKernelPanic'] = True
    # ProvideCurrentCpuInfo - necessário para AMD vanilla patches
    kq['ProvideCurrentCpuInfo'] = True
    # XhciPortLimit - deve estar False para Sonoma 11.3+
    kq['XhciPortLimit'] = False
    
    print(f"  PanicNoKextDump=True, PowerTimeoutKernelPanic=True")
    print(f"  ProvideCurrentCpuInfo=True, XhciPortLimit=False")
    
    # ===================================================================
    # 6. Verificação final do estado
    # ===================================================================
    print("\n" + "=" * 70)
    print("ESTADO FINAL:")
    print("=" * 70)
    
    print("\nBooter Quirks:")
    bq = config['Booter']['Quirks']
    critical_quirks = [
        'AvoidRuntimeDefrag', 'DevirtualiseMmio', 'EnableWriteUnprotector',
        'RebuildAppleMemoryMap', 'SetupVirtualMap', 'SyncRuntimePermissions',
        'ProvideCustomSlide', 'ProtectUefiServices'
    ]
    for q in critical_quirks:
        print(f"  {q}: {bq.get(q)}")
    
    print("\nKexts HABILITADOS:")
    for kext in config['Kernel']['Add']:
        if kext.get('Enabled', True):
            print(f"  ✓ {kext['BundlePath']}")
    
    print("\nKexts DESABILITADOS:")
    for kext in config['Kernel']['Add']:
        if not kext.get('Enabled', True):
            print(f"  ✗ {kext['BundlePath']}")
    
    print(f"\nSSDTs:")
    for acpi in config['ACPI']['Add']:
        status = "✓" if acpi.get('Enabled', True) else "✗"
        print(f"  {status} {acpi['Path']}")
    
    print(f"\nBoot-args: {nvram['boot-args']}")
    
    csr = nvram.get('csr-active-config', b'')
    print(f"CSR: {csr.hex() if isinstance(csr, bytes) else csr}")
    
    print(f"\nSMBIOS: {config['PlatformInfo']['Generic'].get('SystemProductName', 'N/A')}")
    print(f"DmgLoading: {config['Misc']['Security'].get('DmgLoading', 'N/A')}")
    print(f"SecureBootModel: {config['Misc']['Security'].get('SecureBootModel', 'N/A')}")
    print(f"DummyPowerManagement: {config['Kernel']['Emulate'].get('DummyPowerManagement', 'N/A')}")
    
    # Drivers
    print(f"\nDrivers UEFI:")
    for d in config['UEFI']['Drivers']:
        print(f"  {d['Path']} (LoadEarly={d.get('LoadEarly', False)})")
    
    # ===================================================================
    # SALVAR
    # ===================================================================
    with open(CONFIG_PATH, 'wb') as f:
        plistlib.dump(config, f)
    
    print("\n" + "=" * 70)
    print("✓ CONFIG SALVA COM SUCESSO!")
    print("=" * 70)
    
    print("""
INSTRUÇÕES PARA BOOT 9:
1. Ejete o USB com segurança
2. Conecte no notebook e boot pelo USB
3. No menu OpenCore, selecione "Reset NVRAM" primeiro
4. Reinicie e selecione "macOS Base System"
5. Aguarde 5-10 minutos - pode parecer travado mas está processando

SE AINDA REINICIAR:
- Verifique se CSM está DESATIVADO na BIOS
- Verifique se Secure Boot está DESATIVADO
- Tente trocar a porta USB (USB 2.0 vs 3.0)

SE TRAVAR EM PCI/EXITBS:
- Pode precisar aguardar mais tempo (até 15 min na primeira vez)
- Se realmente travar, tire foto da tela para diagnóstico
""")

if __name__ == '__main__':
    main()
