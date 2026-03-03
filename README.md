# Hackintosh: ASUS Vivobook/TUF — AMD Ryzen 7 4800HS (Renoir) + macOS Sonoma

> **Guia completo, testado e documentado** para instalar macOS Sonoma 14.x em notebooks ASUS com processador AMD Ryzen 7 4800HS (Zen 2 / Renoir). Baseado em experiência prática real com todos os problemas encontrados e soluções aplicadas.

---

## ⚠️ Avisos Importantes

- Este é um **notebook AMD** com iGPU Vega (Renoir). A instalação é possível graças ao **NootedRed** e aos patches **AMD Vanilla**.
- **Versão testada e recomendada**: macOS Sonoma 14.7.
- O SMBIOS utilizado é `MacBookPro16,3`.
- **Gere seus próprios seriais SMBIOS** com o GenSMBIOS antes de usar. Os seriais neste repositório são placeholders.
- Neste hardware, a **VRAM da iGPU foi ajustada manualmente para 2GB (2048MB)** via UMAF/Smokeless-UMAF para estabilidade gráfica.
- O fluxo validado inclui **pré-configurar o Wi-Fi no pendrive de instalação** (itlwm) antes do primeiro boot do instalador.

---

## 📋 Perfil do Hardware

| Componente | Detalhe |
|---|---|
| **Notebook** | ASUS Vivobook / TUF Gaming A15 |
| **CPU** | AMD Ryzen 7 4800HS (Zen 2, Renoir, 8C/16T) |
| **iGPU** | AMD Radeon Vega 7 (Renoir) |
| **Wi-Fi/BT** | Intel AX200 (Wi-Fi 6) |
| **Áudio** | Realtek (codec layout `alcid=21`) |
| **Trackpad** | ELAN1203 via I2C (barramento `I2CB`, endereço `0x0015`) |
| **NVMe** | SSD M.2 NVMe interno |
| **Bootloader** | OpenCore 1.0.4+ |
| **SMBIOS** | `MacBookPro16,3` |
| **macOS** | Sonoma 14.7 |

---

## ✅ Status de Compatibilidade (Resultado Final)

| Componente | Status | Notas |
|---|---|---|
| **Boot (Apple Logo)** | ✅ Funciona | Boot limpo, sem verbose |
| **iGPU (Vega)** | ✅ Funciona | Aceleração via NootedRed |
| **Áudio** | ✅ Funciona | AppleALC com `alcid=21` |
| **Bateria** | ✅ Funciona | SMCBatteryManager + ECEnabler |
| **Teclado** | ✅ Funciona | VoodooPS2Controller |
| **Wi-Fi** | ✅ Funciona | `itlwm.kext` + HeliPort.app |
| **Wi-Fi no Instalador** | ✅ Funciona | Com pre-configuração do itlwm no pendrive |
| **Bluetooth** | ✅ Funciona | IntelBluetoothFirmware |
| **USB** | ✅ Funciona | GenericUSBXHCI |
| **NVMe/SSD** | ✅ Funciona | NVMeFix |
| **Brilho da Tela** | ✅ Funciona | SSDT-PNLF + BrightnessKeys |
| **Trackpad (Básico)** | ⚠️ Parcial | Cursor, scroll 2 dedos e clique esquerdo funcionam |
| **Trackpad (Multi-touch)** | ❌ Não funciona | Tap-to-click, clique direito, gestos — limitação AMD GPIO |
| **Wi-Fi Nativo** | ❌ Não funciona | AirportItlwm quebrado no Sonoma 14.4+ |
| **Sleep/Wake** | ⚠️ Parcial | Pode ter problemas |
| **Leitor Digital** | ❌ Não funciona | Sem suporte no macOS |

---

## 📦 Estrutura do Repositório

```
├── efi_macos/                  ← EFI FINAL FUNCIONAL (copiar para pendrive/SSD)
│   └── EFI/
│       ├── BOOT/
│       │   └── BOOTx64.efi
│       └── OC/
│           ├── ACPI/           ← SSDTs compilados
│           ├── Drivers/        ← Drivers UEFI
│           ├── Kexts/          ← Extensões do kernel
│           ├── Resources/      ← Tema/ícones do picker
│           ├── Tools/          ← OpenShell.efi
│           ├── OpenCore.efi
│           └── config.plist    ← Configuração principal
│
├── HackintoshEFI/              ← EFI base/referência original
│   ├── AMD_Vanilla_patches.plist
│   ├── com.apple.recovery.boot/
│   ├── EFI/
│   └── macrecovery/            ← Scripts para baixar macOS
│
├── Scripts de utilidade (*.py, *.ps1, *.bat)
│   ├── gerar-config-plist.py       ← Gera config.plist completo do zero
│   ├── copiar-efi-para-pendrive.py ← Copia EFI para o pendrive (U:)
│   ├── check-config.py             ← Audita e exibe configuração atual
│   ├── check-kexts.py              ← Verifica kexts
│   ├── injetar-wifi-oculto.py      ← Injeta credenciais Wi-Fi no itlwm
│   ├── setup-itlwm.py              ← Setup alternativo de Wi-Fi
│   ├── baixar-macos-recovery.bat   ← Baixa recovery do macOS
│   └── ...outros scripts de fix/diagnóstico
│
└── README.md                   ← Este guia
```

---

## 🗂️ EFI Detalhada — Kexts, SSDTs e Drivers

### ACPI (SSDTs)

| SSDT | Propósito |
|---|---|
| `SSDT-ALS0.aml` | Sensor de luz ambiente falso |
| `SSDT-EC-USBX.aml` | Embedded Controller + USB Power Properties |
| `SSDT-HPET.aml` | Fix de conflitos IRQ do timer |
| `SSDT-PLUG-ALT.aml` | Plugin-type para gerenciamento de energia (AMD) |
| `SSDT-PNLF.aml` | Controle de backlight/brilho da tela |
| `SSDT-XOSI.aml` | Spoof de OS para I2C (finge ser Windows 2015) |

### ACPI Patches

| Patch | Propósito |
|---|---|
| `Change _OSI to XOSI` | Redireciona chamadas _OSI para o SSDT-XOSI, habilitando I2C |

### Kexts (Habilitadas)

| Kext | Propósito |
|---|---|
| `Lilu.kext` | Framework base (OBRIGATÓRIO) |
| `VirtualSMC.kext` | Emula o chip SMC da Apple (OBRIGATÓRIO) |
| `SMCBatteryManager.kext` | Leitura de bateria |
| `SMCLightSensor.kext` | Sensor de luz |
| `SMCProcessorAMD.kext` | Temperaturas da CPU AMD |
| `NootedRed.kext` | Driver da iGPU AMD Vega (Renoir) |
| `AppleALC.kext` | Driver de áudio (`alcid=21`) |
| `ForgedInvariant.kext` | Sincronização TSC para AMD laptops |
| `NVMeFix.kext` | Correções para drives NVMe |
| `IntelBluetoothFirmware.kext` | Firmware Bluetooth Intel |
| `IntelBTPatcher.kext` | Patches BT Intel |
| `BlueToolFixup.kext` | Fix Bluetooth macOS 12+ |
| `VoodooPS2Controller.kext` | Driver PS2 (teclado) |
| `VoodooPS2Keyboard.kext` | Plugin teclado PS2 |
| `VoodooPS2Mouse.kext` | Plugin mouse PS2 (fallback trackpad) |
| `VoodooPS2Trackpad.kext` | Plugin trackpad PS2 |
| `VoodooInput.kext` | Input framework (via PS2) |
| `VoodooI2C.kext` | Driver principal I2C |
| `VoodooI2CServices.kext` | Serviços I2C |
| `VoodooGPIO.kext` | GPIO controller (necessário para carregar I2C) |
| `VoodooI2CHID.kext` | Satélite HID para trackpad I2C |
| `ECEnabler.kext` | Fix large EC fields (bateria) |
| `BrightnessKeys.kext` | Teclas de brilho do teclado |
| `RestrictEvents.kext` | Fix nome CPU e OTA updates |
| `AppleMCEReporterDisabler.kext` | Desabilita MCE Reporter (crash em AMD) |
| `AMFIPass.kext` | Bypass AMFI |
| `itlwm.kext` | Driver Wi-Fi Intel (usa HeliPort.app) |

### Kexts (Desabilitadas — Disponíveis para Teste)

| Kext | Notas |
|---|---|
| `SMCAMDProcessor.kext` | Alternativa para CPU Power Management |
| `AMDRyzenCPUPowerManagement.kext` | Power management AMD (conflita com ForgedInvariant) |
| `GenericUSBXHCI.kext` | USB XHCI genérico (testar se USB falhar) |
| `AirportItlwm.kext` | Wi-Fi Intel nativo — **QUEBRADO no Sonoma 14.4+** |
| `VoodooI2CELAN.kext` | Satélite ELAN — testado, não funcionou nesta máquina com polling |

### Drivers UEFI

| Driver | Propósito |
|---|---|
| `HfsPlus.efi` | Leitura de partições HFS+ |
| `OpenRuntime.efi` | Runtime patches do OpenCore |
| `OpenVariableRuntimeDxe.efi` | Fix variáveis NVRAM |
| `ResetNvramEntry.efi` | Opção de Reset NVRAM no picker |

---

## Boot Args (Argumentos de Inicialização)

```
keepsyms=1 alcid=21 npci=0x3000 amfi_get_out_of_my_way=0x1 revblock=media ipc_control_port_options=0 msgbuf=1048576 -NRedDPDelay -vi2c-force-polling
```

| Argumento | Propósito |
|---|---|
| `keepsyms=1` | Preserva símbolos em kernel panics para diagnóstico |
| `alcid=21` | Layout de áudio Realtek (testado e funcional) |
| `npci=0x3000` | Fix para travamento em "PCI Configuration Begin" |
| `amfi_get_out_of_my_way=0x1` | Desabilita AMFI (necessário para NootedRed) |
| `revblock=media` | Bloqueia check de revisão (RestrictEvents) |
| `ipc_control_port_options=0` | Fix IPC no Sonoma |
| `msgbuf=1048576` | Buffer de log maior para debug |
| `-NRedDPDelay` | Opção NootedRed para DisplayPort |
| `-vi2c-force-polling` | **CRÍTICO**: Força polling no trackpad I2C (evita Kernel Panic no AMD) |

---

## 🔥 Problemas Encontrados e Soluções (Diário de Bordo)

### Problema 1: Boot Travando em `[EB|#LOG:EXITBS:START]`

**Sintoma**: O boot parava completamente na mensagem `EXITBS:START` e nunca avançava.

**Causa**: Conflitos de mapeamento de memória comuns em placas AMD Renoir com o OpenCore.

**Solução**:
- `Booter → Quirks → DevirtualiseMmio = True`
- `Booter → Quirks → RebuildAppleMemoryMap = True`
- `Booter → Quirks → SetupVirtualMap = True`
- `Booter → Quirks → SyncRuntimePermissions = True`
- `Booter → Quirks → AvoidRuntimeDefrag = True`
- `boot-args: npci=0x3000`

---

### Problema 2: Wi-Fi Nativo (AirportItlwm) Morreu no Sonoma 14.4+

**Sintoma**: Após trocar de `itlwm.kext` para `AirportItlwm.kext`, o Wi-Fi sumiu completamente. Nenhuma interface de rede aparecia.

**Causa**: A partir do macOS Sonoma 14.4, a Apple **removeu** o framework `IO80211FamilyLegacy` que o `AirportItlwm` usava para simular Wi-Fi nativo. Sem esse framework, a kext não consegue registrar a interface de rede.

**Solução DEFINITIVA**: Voltar para `itlwm.kext` + usar o app **HeliPort** para gerenciar Wi-Fi.
- `itlwm.kext` → **Enabled: True**
- `AirportItlwm.kext` → **Enabled: False**
- Baixar HeliPort: https://github.com/OpenIntelWireless/HeliPort/releases
- Caso o HeliPort dê erro de "unexpected path", execute no Terminal:
  ```bash
  xattr -cr /Applications/HeliPort.app
  ```

> **Lição**: No Sonoma 14.4+, **nunca** use AirportItlwm com Intel AX200. Use itlwm + HeliPort.

---

### Problema 3: Trackpad — Apenas Modo Básico Funciona (Limitação AMD)

**Sintoma**: O trackpad ELAN1203 move o cursor e permite scroll com dois dedos, mas tap-to-click, clique com dois dedos (botão direito) e gestos avançados não funcionam.

**Causa Raiz (Análise da DSDT)**:
A DSDT do notebook revela que o trackpad está mapeado assim:
```
Device (TPD2) em Scope (_SB.I2CB):
  _HID: "ELAN1203"
  _CID: "PNP0C50" (HID Protocol Device I2C)
  I2cSerialBusV2: Endereço 0x0015 em \_SB.I2CB
  GpioInt: Pino 0x0008 via \_SB.GPIO
```

O problema é que o `VoodooGPIO` (plugin dentro do VoodooI2C) **não suporta os controladores GPIO da AMD** — ele foi feito para Intel LPSS. Quando tenta ler o pino GPIO 0x0008 no hardware AMD, causa um **Page Fault** fatal no kernel.

**Tentativas realizadas**:

| Tentativa | Resultado |
|---|---|
| Remover `-vi2c-force-polling` | ❌ Kernel Panic instantâneo (crash no VoodooGPIO) |
| Desabilitar VoodooGPIO + remover polling | ❌ Boot funciona, mas trackpad morre completamente |
| Trocar VoodooI2CHID → VoodooI2CELAN | ❌ Trackpad não responde (ELAN não funciona com polling mode) |
| Desabilitar VoodooPS2Mouse + PS2Trackpad | ❌ Trackpad morre (são eles que dão o fallback básico) |

**Solução Final**: Manter `-vi2c-force-polling` nos boot-args. O trackpad roda em modo PS2 fallback, dando:
- ✅ Movimento do cursor
- ✅ Scroll com dois dedos
- ✅ Clique esquerdo (botão físico)
- ❌ Tap-to-click, clique direito, gestos avançados

> **Lição para futuros usuários AMD Renoir**: O trackpad I2C ELAN em notebooks ASUS com AMD Renoir é uma das limitações mais duras do Hackintosh. Sem um patch ACPI customizado que remapeie o GPIO para APIC (o que exige conhecimento avançado de ASL e acesso ao pino APIC exato), **o modo polling com funcionalidade básica é o máximo atingível**. A recomendação é usar um mouse externo para produtividade.

---

### Problema 4: Áudio — Encontrando o `alcid` Correto

**Sintoma**: Áudio não funcionava com os layouts padrão (`alcid=1`, `alcid=2`, etc).

**Solução**: Testar múltiplos layouts até encontrar o correto. Nesta máquina, o layout funcional é:
```
alcid=21
```

> **Dica**: Use a referência em https://github.com/acidanthera/AppleALC/wiki/Supported-codecs para descobrir quais layouts seu codec suporta.

---

### Problema 5: Verbose Mode (`-v`)

Para debug durante a instalação e ajustes, mantenha `-v` nos boot-args. **Remova após confirmar que tudo funciona** para ver o boot limpo com a logo da Apple.

Cuidado ao remover: o argumento `-v` pode ser confundido com o `-v` dentro de `-vi2c-force-polling`. Use substituição exata:
```python
# ERRADO (quebra -vi2c-force-polling):
boot_args.replace('-v', '')

# CORRETO:
boot_args = ' '.join([a for a in boot_args.split() if a == '-vi2c-force-polling' or a != '-v'])
```

---

### Problema 6: VRAM da iGPU em valor baixo (instabilidade/limitação gráfica)

**Sintoma**: Em configuração padrão de BIOS, a iGPU pode ficar com memória pré-alocada insuficiente, afetando aceleração gráfica e estabilidade em cargas maiores.

**Solução aplicada nesta máquina**: Ajuste manual de VRAM para **2GB (2048MB)** com **Smokeless-UMAF**.

> **Lição**: Para Ryzen Renoir com NootedRed, manter VRAM em 2GB melhora consistência visual e reduz chance de glitches em uso prolongado.

---

## 📝 Guia Passo a Passo Completo

### Pré-requisitos
- Pendrive USB 16GB+ (recomendado 32GB)
- Notebook ASUS com Ryzen 7 4800HS
- Conexão com internet (cabo Ethernet, tethering USB)
- Windows instalado para preparação
- Python 3.x instalado

### Etapa 0: BIOS/UMAF (crítico antes da instalação)

1. Entre na BIOS e desabilite `Secure Boot`.
2. Acesse o menu avançado via **Smokeless-UMAF**.
3. Ajuste a memória da iGPU (UMA Frame Buffer) para **2GB / 2048MB**.
4. Salve alterações e reinicie.

> Sem esse ajuste, este projeto não reproduz o mesmo nível de estabilidade observado durante as sessões.

### Etapa 1: Baixar macOS Recovery

```powershell
# Na pasta macrecovery/ do OpenCorePkg:
python macrecovery.py -b Mac-226CB3C6A851A671 -m 00000000000000000 download
```

### Etapa 2: Preparar o Pendrive

1. Formate o pendrive como **FAT32** (usando Rufus ou Disk Management)
2. Copie a pasta `com.apple.recovery.boot/` (com BaseSystem.dmg) para a raiz
3. Copie a pasta `EFI/` de `efi_macos/` para a raiz do pendrive

#### Etapa 2.1: Pré-configurar Wi-Fi no pendrive (recomendado)

1. Garanta no `config.plist` da EFI do pendrive:
  - `itlwm.kext` = `Enabled: True`
  - `AirportItlwm.kext` = `Enabled: False`
2. Se for usar rede oculta ou já deixar conexão pronta, edite `injetar-wifi-oculto.py` com `SEU_SSID_AQUI` e `SUA_SENHA_AQUI`.
3. Execute o script no Windows para injetar credenciais no `itlwm.kext` que está no pendrive.
4. Faça boot no instalador já com a EFI preparada para Wi-Fi Intel.

> Observação: o gerenciamento de rede no macOS instalado continua sendo via HeliPort (`itlwm`), não via AirportItlwm no Sonoma 14.4+.

### Etapa 3: Gerar SMBIOS

Use GenSMBIOS (https://github.com/corpnewt/GenSMBIOS):
1. Gere dados para `MacBookPro16,3`
2. Edite o `config.plist` com ProperTree
3. Preencha: `SystemSerialNumber`, `MLB`, `SystemUUID`, `ROM`
4. **Verifique** que o serial retorna "inválido" em https://checkcoverage.apple.com/

### Etapa 4: BIOS do Notebook

| Configuração | Valor |
|---|---|
| Fast Boot | ❌ Desabilitado |
| Secure Boot | ❌ Desabilitado |
| CSM | ❌ Desabilitado |
| IOMMU | ❌ Desabilitado |
| Above 4G Decoding | ✅ Habilitado (senão use `npci=0x3000`) |
| EHCI/XHCI Hand-off | ✅ Habilitado |
| SATA Mode | AHCI |
| VRAM (UMA Frame Buffer) | ✅ **2GB (2048MB)** via Smokeless-UMAF |

### Etapa 5: Instalar macOS

1. Boot pelo pendrive → Selecione OpenCore
2. Abra **Disk Utility** → Formate o disco alvo como **APFS / GPT**
3. Instale macOS Sonoma
4. O sistema reiniciará várias vezes — sempre selecione a opção correta no OpenCore
5. Na primeira inicialização, configure idioma, rede (pule Wi-Fi), conta

### Etapa 6: Pós-instalação

1. Baixe e instale o **HeliPort.app** para gerenciar Wi-Fi
2. Execute `xattr -cr /Applications/HeliPort.app` se der erro de "unexpected path"
3. Conecte ao Wi-Fi via HeliPort
4. Teste áudio, teclado, trackpad, bateria
5. Quando tudo estiver estável, remova `-v` dos boot-args

### Etapa 7: Transferir EFI para o SSD Interno

```bash
# No Terminal do macOS:
# 1. Identificar a partição EFI do SSD:
diskutil list

# 2. Montar a partição EFI (geralmente disk0s1):
sudo diskutil mount disk0s1

# 3. Copiar EFI do pendrive para o SSD:
# (abra o Finder, o disco "EFI" aparecerá na barra lateral)
# Copie a pasta EFI inteira do pendrive para o disco EFI do SSD

# 4. Desligue, remova o pendrive, ligue — deve bootar pelo SSD!
```

---

## 🔧 Scripts de Utilidade

| Script | Descrição |
|---|---|
| `gerar-config-plist.py` | Gera um config.plist completo do zero com todos os patches AMD |
| `copiar-efi-para-pendrive.py` | Sincroniza a pasta `efi_macos/EFI` para o pendrive (`U:`) |
| `check-config.py` | Exibe um resumo da configuração atual do config.plist |
| `check-kexts.py` | Verifica e lista todas as kexts |
| `injetar-wifi-oculto.py` | Injeta SSID/senha diretamente no Info.plist do itlwm |
| `setup-itlwm.py` | Configuração alternativa do itlwm |
| `baixar-macos-recovery.bat` | Atalho para baixar macOS recovery |
| `diagnostico.py` | Script de diagnóstico geral |
| `verify-patches.py` | Verifica integridade dos patches AMD |

> **Nota sobre Wi-Fi**: Os scripts `injetar-wifi-oculto.py` e `setup-itlwm.py` contêm placeholders `SEU_SSID_AQUI` / `SUA_SENHA_AQUI`. Substitua com suas credenciais antes de executar.

---

## ✅ Checklist de Validação Pós-Instalação (Recomendado)

Após subir o macOS e copiar a EFI para o SSD interno, valide:

1. **Boot frio** sem pendrive por pelo menos 3 reinicializações.
2. **Wi-Fi/Bluetooth** estáveis por 30+ minutos (download contínuo + pareamento BT).
3. **Áudio** (alto-falante + fone + microfone) com `alcid=21`.
4. **Vídeo** sem artefatos em uso real (VSCode, navegador com vídeo, monitor externo se aplicável).
5. **USB/NVMe** sem desconexões ou travas em cópia de arquivos grandes.
6. **Trackpad/teclado** dentro da limitação esperada (modo básico para trackpad).

Se qualquer item falhar, revise primeiro: BIOS/UMAF (VRAM 2GB), boot-args, estado das kexts e reset de NVRAM no OpenCore.

---

## 💻 Uso para Desenvolvimento (VSCode / Node.js / React Native)

### Matriz de Viabilidade

| Cenário | Status | Observações práticas |
|---|---|---|
| VSCode + Node.js + npm/yarn/pnpm | ✅ Excelente | Compilação e tooling muito rápidos no Ryzen 7 4800HS |
| Build Android (APK/AAB via Gradle) | ✅ Excelente | Recomendado 16GB+ RAM |
| Build iOS (Xcode) para dispositivo físico | ✅ Funciona | Assinatura e deploy em iPhone/iPad são viáveis |
| Android Emulator | ⚠️ Parcial | Pode variar em desempenho/estabilidade por virtualização em AMD |
| iOS Simulator | ⚠️ Parcial | Em Hackintosh AMD pode apresentar limitações; prefira iPhone físico |
| Docker/containers | ⚠️ Parcial | Dependente de virtualização; valide seu fluxo antes de adotar em produção |

### Boas práticas para trabalho diário

1. Priorize **dispositivo físico** (Android/iOS) para testes de app.
2. Evite updates de macOS no dia do lançamento; atualize primeiro OpenCore + kexts essenciais.
3. Mantenha backup da EFI em pendrive e snapshot/backup do sistema antes de grandes mudanças.
4. Documente toda alteração de BIOS, boot-args e kexts para rollback rápido.

---

## 🔗 Referências e Recursos

- [OpenCore Install Guide (Dortania)](https://dortania.github.io/OpenCore-Install-Guide/)
- [AMD Vanilla Patches](https://github.com/AMD-OSX/AMD_Vanilla)
- [NootedRed (ChefKiss)](https://github.com/ChefKissInc/NootedRed)
- [itlwm / AirportItlwm](https://github.com/OpenIntelWireless/itlwm)
- [HeliPort](https://github.com/OpenIntelWireless/HeliPort)
- [VoodooI2C](https://github.com/VoodooI2C/VoodooI2C)
- [AppleALC Supported Codecs](https://github.com/acidanthera/AppleALC/wiki/Supported-codecs)
- [SSDTTime](https://github.com/corpnewt/SSDTTime)
- [GenSMBIOS](https://github.com/corpnewt/GenSMBIOS)
- [Smokeless-UMAF](https://github.com/DavidS95/Smokeless_UMAF)
- [AMD OS X Discord](https://discord.gg/EfCYAJW)
- [r/Hackintosh](https://www.reddit.com/r/hackintosh/)

## 📄 Licença

Este projeto é fornecido "como está" para fins educacionais. macOS é marca registrada da Apple Inc. O uso do macOS em hardware não-Apple pode violar os termos de serviço da Apple. Use por sua conta e risco.
