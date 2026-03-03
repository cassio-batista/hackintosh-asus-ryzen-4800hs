#!/usr/bin/env python3
"""
Gera config.plist completo para OpenCore - ASUS Vivobook AMD Ryzen 7 4800HS
Baseado no Sample.plist do OpenCore 1.0.6 + AMD Vanilla patches
"""

import plistlib
import os
import uuid
import hashlib
import random
import struct

BASE = r'C:\Users\cassi\git\New folder\HackintoshEFI'
EFI = os.path.join(BASE, 'EFI', 'OC')
CONFIG_PATH = os.path.join(EFI, 'config.plist')
SAMPLE_PATH = CONFIG_PATH  # Sample.plist was renamed to config.plist
AMD_PATCHES_PATH = os.path.join(BASE, 'AMD_Vanilla_patches.plist')
KEXTS_DIR = os.path.join(EFI, 'Kexts')
ACPI_DIR = os.path.join(EFI, 'ACPI')
DRIVERS_DIR = os.path.join(EFI, 'Drivers')

# Hardware: AMD Ryzen 7 4800HS - 8 cores
CORE_COUNT = 8
SMBIOS_MODEL = 'MacBookPro16,3'  # T2 chip MacBook, mejor compatibility with NootedRed

def load_plist(path):
    with open(path, 'rb') as f:
        return plistlib.load(f)

def save_plist(data, path):
    with open(path, 'wb') as f:
        plistlib.dump(data, f, sort_keys=False)

def generate_serial():
    """Generate a plausible serial number for MacBookPro16,3"""
    # Format: CXXXXXXXXXX (11 chars)
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ0123456789'
    prefix = 'C02'
    mid = ''.join(random.choices(chars, k=5))
    suffix = 'MD6T'  # Common suffix for MacBookPro16,3
    return prefix + mid + suffix

def generate_mlb():
    """Generate a plausible MLB (Board Serial)"""
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ0123456789'
    return 'C02' + ''.join(random.choices(chars, k=14))

def generate_uuid():
    return str(uuid.uuid4()).upper()

def generate_rom():
    """Generate a random ROM (MAC address bytes)"""
    return bytes([random.randint(0, 255) for _ in range(6)])

def get_kext_info(kext_path):
    """Read Info.plist from a kext and return bundle info"""
    info_path = os.path.join(kext_path, 'Contents', 'Info.plist')
    if not os.path.exists(info_path):
        return None
    with open(info_path, 'rb') as f:
        info = plistlib.load(f)
    return {
        'BundleIdentifier': info.get('CFBundleIdentifier', ''),
        'BundleExecutable': info.get('CFBundleExecutable', ''),
        'BundleVersion': info.get('CFBundleVersion', '1.0'),
    }

def build_kext_entry(kext_name, bundle_path='', exec_path='', bundle_id='', enabled=True, min_kernel='', max_kernel=''):
    return {
        'Arch': 'x86_64',
        'BundlePath': bundle_path or kext_name,
        'Comment': '',
        'Enabled': enabled,
        'ExecutablePath': exec_path,
        'MaxKernel': max_kernel,
        'MinKernel': min_kernel,
        'PlistPath': 'Contents/Info.plist',
    }

def build_kext_entries():
    """Build ordered list of kext entries for Kernel > Add"""
    entries = []

    # Define loading order (critical! Lilu must load first, then VirtualSMC, etc.)
    kext_order = [
        # 1. Lilu (must be first)
        'Lilu.kext',
        # 2. VirtualSMC and plugins
        'VirtualSMC.kext',
        'SMCBatteryManager.kext',
        'SMCLightSensor.kext',
        'SMCProcessorAMD.kext',
        'SMCRadeonSensors.kext',
        # 3. GPU
        'NootedRed.kext',
        # 4. Audio
        'AppleALC.kext',
        # 5. Invariant TSC
        'ForgedInvariant.kext',
        # 6. NVMe
        'NVMeFix.kext',
        # 7. WiFi
        'AirportItlwm.kext',
        # 8. Bluetooth
        'IntelBluetoothFirmware.kext',
        'IntelBTPatcher.kext',
        'BlueToolFixup.kext',
        # 9. Ethernet (may be broken kext but include disabled)
        'RealtekRTL8111.kext',
        # 10. Input - PS2
        'VoodooPS2Controller.kext',
        # PS2 plugins
        'VoodooPS2Controller.kext/Contents/PlugIns/VoodooPS2Keyboard.kext',
        'VoodooPS2Controller.kext/Contents/PlugIns/VoodooPS2Mouse.kext',
        'VoodooPS2Controller.kext/Contents/PlugIns/VoodooPS2Trackpad.kext',
        'VoodooPS2Controller.kext/Contents/PlugIns/VoodooInput.kext',
        # 11. Input - I2C
        'VoodooI2C.kext',
        'VoodooI2C.kext/Contents/PlugIns/VoodooI2CServices.kext',
        'VoodooI2C.kext/Contents/PlugIns/VoodooGPIO.kext',
        'VoodooI2C.kext/Contents/PlugIns/VoodooInput.kext',
        'VoodooI2CHID.kext',
        # 12. Other utilities
        'ECEnabler.kext',
        'BrightnessKeys.kext',
        'RestrictEvents.kext',
        'AppleMCEReporterDisabler.kext',
    ]

    for kext_rel in kext_order:
        kext_full = os.path.join(KEXTS_DIR, kext_rel)
        if not os.path.isdir(kext_full):
            print(f'  SKIP (not found): {kext_rel}')
            continue

        info = get_kext_info(kext_full)

        # Determine executable path
        if info and info['BundleExecutable']:
            exec_path = f'Contents/MacOS/{info["BundleExecutable"]}'
            # Verify it actually exists
            exec_full = os.path.join(kext_full, 'Contents', 'MacOS', info['BundleExecutable'])
            if not os.path.exists(exec_full):
                exec_path = ''  # Dummy kext or broken
        else:
            exec_path = ''  # No executable (dummy kext)

        # Special cases
        enabled = True
        if 'RealtekRTL8111' in kext_rel:
            enabled = False  # Broken kext - disable
            exec_path = ''

        entry = build_kext_entry(
            kext_name=os.path.basename(kext_rel),
            bundle_path=kext_rel.replace('\\', '/'),
            exec_path=exec_path,
            enabled=enabled,
        )
        entries.append(entry)
        status = 'OK' if enabled else 'DISABLED'
        print(f'  {status}: {kext_rel} -> exec={exec_path}')

    return entries

def build_acpi_entries():
    """Build ACPI > Add entries for SSDTs"""
    entries = []
    for f in sorted(os.listdir(ACPI_DIR)):
        if f.endswith('.aml'):
            entries.append({
                'Comment': f.replace('.aml', ''),
                'Enabled': True,
                'Path': f,
            })
            print(f'  ACPI: {f}')
    return entries

def build_driver_entries():
    """Build UEFI > Drivers entries"""
    entries = []
    for f in sorted(os.listdir(DRIVERS_DIR)):
        if f.endswith('.efi'):
            entries.append({
                'Arguments': '',
                'Comment': '',
                'Enabled': True,
                'LoadEarly': f == 'OpenRuntime.efi',
                'Path': f,
            })
            print(f'  Driver: {f} (LoadEarly={f == "OpenRuntime.efi"})')
    return entries

def apply_core_count_patches(patches):
    """Set core count to 8 in AMD Vanilla patches"""
    count = 0
    for patch in patches:
        comment = patch.get('Comment', '')
        if 'cpuid_cores_per_package' in comment.lower():
            replace_bytes = bytearray(patch['Replace'])
            # The core count is at byte index 1 (after the opcode: B8=mov eax or BA=mov edx)
            if len(replace_bytes) >= 2:
                replace_bytes[1] = CORE_COUNT
                patch['Replace'] = bytes(replace_bytes)
                count += 1
                print(f'  Core patch applied: {comment} -> byte[1] = 0x{CORE_COUNT:02X}')
    print(f'  Total core count patches applied: {count}')
    return patches

def main():
    print('=' * 60)
    print(' GERANDO config.plist - OpenCore 1.0.6')
    print(' ASUS Vivobook - AMD Ryzen 7 4800HS (Zen 2 / Renoir)')
    print('=' * 60)

    # Load Sample/config.plist
    print('\n[1] Carregando Sample.plist...')
    config = load_plist(SAMPLE_PATH)
    print(f'  Loaded. Top-level keys: {list(config.keys())}')

    # Load AMD Vanilla patches
    print('\n[2] Carregando AMD Vanilla patches...')
    amd_patches = load_plist(AMD_PATCHES_PATH)
    kernel_patches = amd_patches['Kernel']['Patch']
    print(f'  {len(kernel_patches)} patches carregados')

    # ===== ACPI =====
    print('\n[3] Configurando ACPI...')
    acpi_add = build_acpi_entries()
    config['ACPI']['Add'] = acpi_add
    config['ACPI']['Delete'] = []
    config['ACPI']['Patch'] = []
    config['ACPI']['Quirks'] = {
        'FadtEnableReset': False,
        'NormalizeHeaders': False,
        'RebaseRegions': False,
        'ResetHwSig': False,
        'ResetLogoStatus': True,
        'SyncTableIds': False,
    }

    # ===== Booter =====
    print('\n[4] Configurando Booter...')
    config['Booter']['MmioWhitelist'] = []
    config['Booter']['Patch'] = []
    config['Booter']['Quirks'] = {
        'AllowRelocationBlock': False,
        'AvoidRuntimeDefrag': True,
        'DevirtualiseMmio': False,
        'DisableSingleUser': False,
        'DisableVariableWrite': False,
        'DiscardHibernateMap': False,
        'EnableSafeModeSlide': True,
        'EnableWriteUnprotector': False,
        'ForceBooterSignature': False,
        'ForceExitBootServices': False,
        'ProtectMemoryRegions': False,
        'ProtectSecureBoot': False,
        'ProtectUefiServices': False,
        'ProvideCustomSlide': True,
        'ProvideMaxSlide': 0,
        'RebuildAppleMemoryMap': True,
        'ResizeAppleGpuBars': -1,
        'SetupVirtualMap': True,
        'SignalAppleOS': False,
        'SyncRuntimePermissions': True,
    }
    print('  Booter quirks configurados (AMD Zen 2)')

    # ===== DeviceProperties =====
    print('\n[5] Configurando DeviceProperties...')
    config['DeviceProperties'] = {
        'Add': {},
        'Delete': {},
    }
    print('  DeviceProperties limpo (NootedRed configura GPU automaticamente)')

    # ===== Kernel =====
    print('\n[6] Configurando Kernel...')

    # Kexts
    print('  Adicionando kexts:')
    kext_entries = build_kext_entries()
    config['Kernel']['Add'] = kext_entries

    # AMD Vanilla patches with core count
    print('\n  Aplicando AMD Vanilla patches:')
    patched = apply_core_count_patches(kernel_patches)
    config['Kernel']['Patch'] = patched
    config['Kernel']['Block'] = []
    config['Kernel']['Force'] = []
    config['Kernel']['Scheme'] = {
        'CustomKernel': False,
        'FuzzyMatch': True,
        'KernelArch': 'x86_64',
        'KernelCache': 'Auto',
    }

    # Emulate - not needed for bare metal AMD
    config['Kernel']['Emulate'] = {
        'Cpuid1Data': b'',
        'Cpuid1Mask': b'',
        'DummyPowerManagement': True,  # Important for AMD!
        'MaxKernel': '',
        'MinKernel': '',
    }

    config['Kernel']['Quirks'] = {
        'AppleCpuPmCfgLock': False,
        'AppleXcpmCfgLock': False,
        'AppleXcpmExtraMsrs': False,
        'AppleXcpmForceBoost': False,
        'CustomPciSerialDevice': False,
        'CustomSMBIOSGuid': False,
        'DisableIoMapper': False,
        'DisableIoMapperMapping': False,
        'DisableLinkeditJettison': True,
        'DisableRtcChecksum': False,
        'ExtendBTFeatureFlags': False,
        'ExternalDiskIcons': False,
        'ForceAquantiaEthernet': False,
        'ForceSecureBootScheme': False,
        'IncreasePciBarSize': False,
        'LapicKernelPanic': False,
        'LegacyCommpage': False,
        'PanicNoKextDump': True,
        'PowerTimeoutKernelPanic': True,
        'ProvideCurrentCpuInfo': True,  # Essential for AMD!
        'SetApfsTrimTimeout': -1,
        'ThirdPartyDrives': False,
        'XhciPortLimit': False,
    }
    print('  Kernel quirks configurados')

    # ===== Misc =====
    print('\n[7] Configurando Misc...')
    config['Misc']['BlessOverride'] = []
    config['Misc']['Boot'] = {
        'ConsoleAttributes': 0,
        'HibernateMode': 'None',
        'HibernateSkipsPicker': True,
        'HideAuxiliary': True,
        'LauncherOption': 'Disabled',
        'LauncherPath': 'Default',
        'PickerAttributes': 17,
        'PickerMode': 'External',
        'PickerVariant': 'Auto',
        'PollAppleHotKeys': True,
        'ShowPicker': True,
        'TakeoffDelay': 0,
        'Timeout': 5,
    }
    config['Misc']['Debug'] = {
        'AppleDebug': True,
        'ApplePanic': True,
        'DisableWatchDog': True,
        'DisplayDelay': 0,
        'DisplayLevel': 2147483650,  # 0x80000002
        'LogModules': '*',
        'SysReport': False,
        'Target': 67,  # 0x43 = serial + file + display
    }
    config['Misc']['Entries'] = []
    config['Misc']['Security'] = {
        'AllowSetDefault': True,
        'ApECID': 0,
        'AuthRestart': False,
        'BlacklistAppleUpdate': True,
        'DmgLoading': 'Signed',
        'ExposeSensitiveData': 6,
        'HaltLevel': 2147483648,
        'PasswordHash': b'',
        'PasswordSalt': b'',
        'ScanPolicy': 0,
        'SecureBootModel': 'Disabled',  # Disable for initial install, enable later
        'Vault': 'Optional',
    }
    config['Misc']['Serial'] = {
        'Custom': {
            'BaudRate': 115200,
            'ClockRate': 1843200,
            'Init': False,
            'Override': False,
            'PciDeviceInfo': b'\xff\xff\xff\xff',
            'RegisterAccessWidth': 8,
            'RegisterBase': 0,
            'RegisterStride': 1,
            'UseForConsole': False,
            'UseMmio': False,
        },
        'Init': False,
        'Override': False,
    }
    config['Misc']['Tools'] = [
        {
            'Arguments': '',
            'Auxiliary': True,
            'Comment': 'OpenShell',
            'Enabled': True,
            'Flavour': 'Auto',
            'Name': 'OpenShell',
            'Path': 'OpenShell.efi',
            'RealPath': False,
            'TextMode': False,
        }
    ]
    print('  Misc configurado (Debug habilitado, SecureBoot desabilitado)')

    # ===== NVRAM =====
    print('\n[8] Configurando NVRAM...')
    config['NVRAM'] = {
        'Add': {
            '4D1EDE05-38C7-4A6A-9CC6-4BCCA8B38C14': {
                'DefaultBackgroundColor': b'\x00\x00\x00\x00',
                'UIScale': b'\x01',
            },
            '4D1FDA02-38C7-4A6A-9CC6-4BCCA8B30102': {
                'rtc-blacklist': b'',
            },
            '7C436110-AB2A-4BBB-A880-FE41995C9F82': {
                'SystemAudioVolume': b'\x46',
                'boot-args': '-v keepsyms=1 debug=0x100 alcid=21 npci=0x2000',
                'csr-active-config': b'\x03\x08\x00\x00',  # SIP partially disabled
                'prev-lang:kbd': b'en-US:0',
                'run-efi-updater': 'No',
            },
        },
        'Delete': {
            '4D1EDE05-38C7-4A6A-9CC6-4BCCA8B38C14': [
                'DefaultBackgroundColor',
                'UIScale',
            ],
            '4D1FDA02-38C7-4A6A-9CC6-4BCCA8B30102': [
                'rtc-blacklist',
            ],
            '7C436110-AB2A-4BBB-A880-FE41995C9F82': [
                'boot-args',
                'csr-active-config',
            ],
        },
        'LegacyOverwrite': False,
        'LegacySchema': {},
        'WriteFlash': True,
    }
    print('  boot-args: -v keepsyms=1 debug=0x100 alcid=21 npci=0x2000')
    print('  SIP parcialmente desabilitado para instalacao')

    # ===== PlatformInfo (SMBIOS) =====
    print('\n[9] Configurando PlatformInfo (SMBIOS)...')
    serial = generate_serial()
    mlb = generate_mlb()
    smuuid = generate_uuid()
    rom = generate_rom()

    config['PlatformInfo'] = {
        'Automatic': True,
        'CustomMemory': False,
        'Generic': {
            'AdviseFeatures': False,
            'MaxBIOSVersion': False,
            'MLB': mlb,
            'ProcessorType': 0,
            'ROM': rom,
            'SpoofVendor': True,
            'SystemMemoryStatus': 'Auto',
            'SystemProductName': SMBIOS_MODEL,
            'SystemSerialNumber': serial,
            'SystemUUID': smuuid,
        },
        'UpdateDataHub': True,
        'UpdateNVRAM': True,
        'UpdateSMBIOS': True,
        'UpdateSMBIOSMode': 'Create',
    }
    print(f'  SMBIOS: {SMBIOS_MODEL}')
    print(f'  Serial: {serial}')
    print(f'  MLB: {mlb}')
    print(f'  UUID: {smuuid}')
    print(f'  ROM: {rom.hex()}')
    print('  AVISO: Gere valores proprios com GenSMBIOS antes de usar iCloud/iMessage!')

    # ===== UEFI =====
    print('\n[10] Configurando UEFI...')
    driver_entries = build_driver_entries()

    config['UEFI'] = {
        'APFS': {
            'EnableJumpstart': True,
            'GlobalConnect': False,
            'HideVerbose': True,
            'JumpstartHotPlug': False,
            'MinDate': 0,
            'MinVersion': 0,
        },
        'AppleInput': {
            'AppleEvent': 'Builtin',
            'CustomDelays': False,
            'GraphicsInputMirroring': True,
            'KeyInitialDelay': 50,
            'KeySubsequentDelay': 5,
            'PointerSpeedDiv': 1,
            'PointerSpeedMul': 1,
        },
        'Audio': {
            'AudioCodec': 0,
            'AudioDevice': '',
            'AudioOutMask': -1,
            'AudioSupport': False,
            'DisconnectHda': False,
            'MaximumGain': -15,
            'MinimumAssistGain': -30,
            'MinimumAudibleGain': -128,
            'PlayChime': 'Auto',
            'ResetTrafficClass': False,
            'SetupDelay': 0,
        },
        'ConnectDrivers': True,
        'Drivers': driver_entries,
        'Input': {
            'KeyFiltering': False,
            'KeyForgetThreshold': 5,
            'KeySupport': True,
            'KeySupportMode': 'Auto',
            'KeySwap': False,
            'PointerSupport': False,
            'PointerSupportMode': '',
            'TimerResolution': 50000,
        },
        'Output': {
            'ClearScreenOnModeSwitch': False,
            'ConsoleFont': '',
            'ConsoleMode': 'Max',
            'DirectGopRendering': False,
            'ForceResolution': False,
            'GopBurstMode': False,
            'GopPassThrough': 'Disabled',
            'IgnoreTextInGraphics': False,
            'InitialMode': 'Auto',
            'ProvideConsoleGop': True,
            'ReconnectGraphicsOnConnect': False,
            'ReconnectOnResChange': False,
            'ReplaceTabWithSpace': False,
            'Resolution': 'Max',
            'SanitiseClearScreen': False,
            'TextRenderer': 'BuiltinGraphics',
            'UIScale': 0,
            'UgaPassThrough': False,
        },
        'ProtocolOverrides': {
            'AppleAudio': False,
            'AppleBootPolicy': False,
            'AppleDebugLog': False,
            'AppleEg2Info': False,
            'AppleFramebufferInfo': False,
            'AppleImageConversion': False,
            'AppleImg4Verification': False,
            'AppleKeyMap': False,
            'AppleRtcRam': False,
            'AppleSecureBoot': False,
            'AppleSmcIo': False,
            'AppleUserInterfaceTheme': False,
            'DataHub': False,
            'DeviceProperties': False,
            'FirmwareVolume': False,
            'HashServices': False,
            'OSInfo': False,
            'PciIo': False,
            'UnicodeCollation': False,
        },
        'Quirks': {
            'ActivateHpetSupport': False,
            'DisableSecurityPolicy': False,
            'EnableVectorAcceleration': True,
            'EnableVmx': False,
            'ExitBootServicesDelay': 0,
            'ForceOcWriteFlash': False,
            'ForgeUefiSupport': False,
            'IgnoreInvalidFlexRatio': False,
            'ReleaseUsbOwnership': False,
            'ReloadOptionRoms': False,
            'RequestBootVarRouting': True,
            'ResizeGpuBars': -1,
            'ResizeUsePciRbIo': False,
            'ShimRetainProtocol': False,
            'TscSyncTimeout': 0,
            'UnblockFsConnect': False,
        },
    }
    print('  UEFI configurado')

    # ===== Save =====
    print('\n[11] Salvando config.plist...')
    save_plist(config, CONFIG_PATH)
    print(f'  Salvo em: {CONFIG_PATH}')
    size = os.path.getsize(CONFIG_PATH)
    print(f'  Tamanho: {size} bytes')

    # Validate
    print('\n[12] Validacao...')
    verify = load_plist(CONFIG_PATH)
    print(f'  Kexts no config: {len(verify["Kernel"]["Add"])}')
    print(f'  Patches no config: {len(verify["Kernel"]["Patch"])}')
    print(f'  SSDTs no config: {len(verify["ACPI"]["Add"])}')
    print(f'  Drivers no config: {len(verify["UEFI"]["Drivers"])}')
    print(f'  SMBIOS: {verify["PlatformInfo"]["Generic"]["SystemProductName"]}')

    print('\n' + '=' * 60)
    print(' CONFIG.PLIST GERADO COM SUCESSO!')
    print('=' * 60)
    print('\nPROXIMOS PASSOS:')
    print('  1. Baixar macOS Recovery')
    print('  2. Copiar EFI + Recovery para pendrive')
    print('  3. Configurar BIOS:')
    print('     - Desabilitar Secure Boot')
    print('     - Desabilitar Fast Boot')
    print('     - Habilitar UEFI mode')
    print('     - Desabilitar CSM')
    print('  4. Boot pelo pendrive')
    print('  5. Pos-instalacao: GenSMBIOS para serial valido')

if __name__ == '__main__':
    main()
