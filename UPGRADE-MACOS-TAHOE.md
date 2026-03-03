# Guia de Upgrade: macOS Sonoma 14.7 → macOS 16 Tahoe

> **Branch**: `upgrade/macos-tahoe`
> **Base estável**: `main` (Sonoma 14.7 funcional)
> **Data da análise**: Março 2026

---

## 📊 Análise de Viabilidade

### Mapeamento de Kernel

| macOS | Nome | Darwin Kernel | Status |
|---|---|---|---|
| 14.x | Sonoma | 23.x | ✅ Atual, funcional |
| 15.x | Sequoia | 24.x | ⏭️ Intermediário |
| 16.x | Tahoe | 25.x | 🎯 Alvo deste upgrade |

### Veredicto dos AMD Vanilla Patches

**RESULTADO: COMPATÍVEIS** — Todos os patches críticos já cobrem `MaxKernel: 25.99.99`.

| Patch | Range | Cobre Tahoe? |
|---|---|---|
| `_cpuid_set_info \| Force cpuid_cores_per_package \| 13.3+` | 22.4.0 → 25.99.99 | ✅ |
| `_commpage_populate \| Remove rdmsr` | 17.0.0 → 25.99.99 | ✅ |
| `_cpuid_set_cache_info \| Set CPUID proper` | 17.0.0 → 25.99.99 | ✅ |
| `_cpuid_set_generic_info \| Remove wrmsr(0x8B)` | 17.0.0 → 25.99.99 | ✅ |
| `_cpuid_set_generic_info \| Replace rdmsr(0x8B)` | 17.0.0 → 25.99.99 | ✅ |
| `_cpuid_set_generic_info \| Set flag=1` | 17.0.0 → 25.99.99 | ✅ |
| `_cpuid_set_generic_info \| Disable check leaf7 (15.0+)` | 24.0.0 → 25.99.99 | ✅ |
| `Bypass GenuineIntel check panic (12.0+)` | 21.0.0 → 25.99.99 | ✅ |
| `Force CPUFAMILY_INTEL_PENRYN (11.3+)` | 20.4.0 → 25.99.99 | ✅ |
| `_i386_init \| Remove 3 rdmsr` | 17.0.0 → 25.99.99 | ✅ |
| `Remove version check and panic` | 17.0.0 → 25.99.99 | ✅ |
| `probeBusGated \| Disable 10 bit tags` | 21.0.0 → 25.99.99 | ✅ |
| `thread_quantum_expire \| Remove non-monotonic time panic` | 21.0.0 → 25.99.99 | ✅ |
| `thread_invoke, thread_dispatch \| Remove panic` | 21.0.0 → 25.99.99 | ✅ |

> **IMPORTANTE**: Mesmo com os patches cobrindo o range, a Apple pode alterar as assinaturas de bytes no kernel 25.x. Caso algum patch falhe, será necessário baixar patches atualizados do repositório [AMD_Vanilla](https://github.com/AMD-OSX/AMD_Vanilla).

---

## 🔴 Bloqueadores e Riscos

### 1. NootedRed (CRÍTICO — Bloqueador #1)

- **Versão atual**: 0.8.3
- **Problema**: NootedRed é o driver da iGPU AMD Vega (Renoir). É desenvolvido pelo ChefKiss e historicamente demora semanas a meses para receber suporte a novas versões do macOS.
- **Risco**: Se o NootedRed não suportar Tahoe, **não haverá aceleração gráfica** — o sistema será inutilizável para trabalho.
- **Ação**: Verificar https://github.com/ChefKissInc/NootedRed/releases antes de tentar qualquer upgrade.
- **Critério de GO/NO-GO**: Só prossiga quando houver release ou commit do NootedRed que mencione explicitamente suporte a macOS 16 / Tahoe / kernel 25.

### 2. itlwm / Wi-Fi Intel (Alto Risco)

- **Versão atual**: 2.3.0
- **Problema**: A cada major release do macOS, o framework de rede muda. itlwm 2.3.0 foi construído para Sonoma. Pode não carregar no Tahoe.
- **Ação**: Verificar https://github.com/OpenIntelWireless/itlwm/releases por releases compatíveis com Tahoe.
- **Impacto se falhar**: Sem Wi-Fi (mas pode usar USB tethering ou Ethernet temporariamente).

### 3. SMBIOS MacBookPro16,3 (Médio Risco)

- **Versão atual**: MacBookPro16,3 (Intel, lançado 2020)
- **Problema**: A Apple pode descontinuar suporte a SMBIOS antigos em novas versões. MacBookPro16,3 é um modelo Intel de 2020 — pode ser "cortado" no Tahoe.
- **Ação**: Verificar a lista de Macs compatíveis com macOS 16 em https://support.apple.com/pt-br/macos-system-requirements
- **Alternativa**: Se MacBookPro16,3 for removido, será necessário migrar para um SMBIOS mais recente (ex: `MacBookPro16,1` ou outro modelo ainda suportado). Isso exige gerar novos seriais.

### 4. Boot-args (Baixo Risco)

- `amfi_get_out_of_my_way=0x1` — Pode precisar de ajuste se a Apple mudar a implementação do AMFI.
- `ipc_control_port_options=0` — Introduzido para Sonoma, pode mudar.
- `-vi2c-force-polling` — Não deve mudar (é flag do VoodooI2C, não do kernel).

---

## 📦 Kexts — Versões Atuais vs Necessárias

| Kext | Atual | Precisa Update? | Prioridade | Repositório |
|---|---|---|---|---|
| **Lilu** | 1.7.1 | ✅ Sim | 🔴 Crítica | [acidanthera/Lilu](https://github.com/acidanthera/Lilu/releases) |
| **VirtualSMC** | 1.3.7 | ✅ Sim | 🔴 Crítica | [acidanthera/VirtualSMC](https://github.com/acidanthera/VirtualSMC/releases) |
| **NootedRed** | 0.8.3 | ✅ Sim | 🔴 BLOQUEADOR | [ChefKissInc/NootedRed](https://github.com/ChefKissInc/NootedRed/releases) |
| **AppleALC** | 1.9.6 | ✅ Sim | 🟡 Alta | [acidanthera/AppleALC](https://github.com/acidanthera/AppleALC/releases) |
| **itlwm** | 2.3.0 | ✅ Sim | 🔴 Crítica | [OpenIntelWireless/itlwm](https://github.com/OpenIntelWireless/itlwm/releases) |
| **IntelBluetoothFirmware** | 2.4.0 | ✅ Provável | 🟡 Alta | [OpenIntelWireless/IntelBluetoothFirmware](https://github.com/OpenIntelWireless/IntelBluetoothFirmware/releases) |
| **BlueToolFixup** | 2.7.1 | ✅ Provável | 🟡 Alta | (incluso no BrcmPatchRAM) |
| **VoodooI2C** | 2.9.1 | ⚠️ Talvez | 🟡 Média | [VoodooI2C/VoodooI2C](https://github.com/VoodooI2C/VoodooI2C/releases) |
| **VoodooPS2Controller** | 2.3.7 | ⚠️ Talvez | 🟡 Média | [acidanthera/VoodooPS2](https://github.com/acidanthera/VoodooPS2/releases) |
| **ECEnabler** | 1.0.6 | ⚠️ Talvez | 🟢 Baixa | [1Revenger1/ECEnabler](https://github.com/1Revenger1/ECEnabler/releases) |
| **RestrictEvents** | 1.1.6 | ✅ Sim | 🟡 Alta | [acidanthera/RestrictEvents](https://github.com/acidanthera/RestrictEvents/releases) |
| **NVMeFix** | 1.1.3 | ⚠️ Talvez | 🟢 Baixa | [acidanthera/NVMeFix](https://github.com/acidanthera/NVMeFix/releases) |
| **ForgedInvariant** | 1.5.0 | ⚠️ Talvez | 🟡 Média | [ChefKissInc/ForgedInvariant](https://github.com/ChefKissInc/ForgedInvariant/releases) |
| **AMFIPass** | 1.4.1 | ✅ Provável | 🟡 Alta | [dhinakg/AMFIPass](https://github.com/dhinakg/AMFIPass/releases) |
| **BrightnessKeys** | 1.0.3 | ⚠️ Talvez | 🟢 Baixa | [acidanthera/BrightnessKeys](https://github.com/acidanthera/BrightnessKeys/releases) |

### Ordem de Atualização (OBRIGATÓRIA)

1. **Lilu** (sempre primeiro — é dependência de quase tudo)
2. **VirtualSMC** + plugins SMC (SMCBatteryManager, SMCProcessorAMD, etc.)
3. **NootedRed** (GPU — sem isso, tela preta)
4. **AppleALC** (áudio)
5. **itlwm** + **IntelBluetoothFirmware** + **BlueToolFixup** (Wi-Fi/BT)
6. **RestrictEvents**, **AMFIPass**, **ForgedInvariant**
7. **VoodooI2C**, **VoodooPS2Controller** (input)
8. **ECEnabler**, **NVMeFix**, **BrightnessKeys** (outros)

---

## 🔧 Alterações Necessárias no config.plist

### 1. AMD Vanilla Patches
- **Status**: Já cobrem kernel 25.x ✅
- **Ação recomendada**: Mesmo assim, substituir pelos patches mais recentes do [AMD_Vanilla](https://github.com/AMD-OSX/AMD_Vanilla) para garantir que novas correções estejam incluídas.

### 2. SecureBootModel
- **Atual**: `Disabled`
- **Ação**: Manter `Disabled` para o upgrade. Pode ser ajustado depois para `Default` se tudo funcionar.

### 3. SMBIOS
- **Atual**: `MacBookPro16,3`
- **Ação**: Verificar se ainda é suportado no Tahoe. Se não for, migrar para SMBIOS compatível e gerar novos seriais.

### 4. Boot-args
- **Atual**: `keepsyms=1 alcid=21 npci=0x3000 amfi_get_out_of_my_way=0x1 revblock=media ipc_control_port_options=0 msgbuf=1048576 -NRedDPDelay -vi2c-force-polling`
- **Ação**: Adicionar `-v` (verbose) durante o upgrade para diagnóstico. Verificar se `ipc_control_port_options=0` ainda é necessário no Tahoe.

### 5. csr-active-config
- **Atual**: `FF0F0000` (SIP totalmente desabilitado)
- **Ação**: Manter durante o upgrade.

---

## 📥 Baixar Recovery do macOS 16 Tahoe

### Via macrecovery.py (já disponível no repositório)

```powershell
cd HackintoshEFI\macrecovery
python macrecovery.py -b Mac-CFF7D910A743CAAF -m 00000000000000000 -os latest download
```

### Via script atualizado (baixar-macos-recovery.bat)

O script foi atualizado nesta branch para incluir a opção macOS 16 Tahoe.

---

## 📝 Plano de Execução Passo a Passo

### Fase 0: Preparação (ANTES de tocar em qualquer coisa)

- [ ] Fazer backup completo da EFI atual (copiar `efi_macos/EFI/` para local seguro)
- [ ] Verificar se NootedRed tem release para Tahoe
- [ ] Verificar se itlwm tem release para Tahoe
- [ ] Verificar se MacBookPro16,3 é suportado no Tahoe
- [ ] Se qualquer um dos 3 itens acima falhar → **PARAR. Não prosseguir.**

### Fase 1: Atualizar Kexts

- [ ] Baixar última versão de cada kext (tabela acima)
- [ ] Substituir os `.kext` em `efi_macos/EFI/OC/Kexts/`
- [ ] **NÃO** mudar a ordem no config.plist (respeitar ordem de carregamento)
- [ ] Se alguma kext tiver mudado de BundlePath/ExecutablePath, atualizar no config.plist

### Fase 2: Atualizar OpenCore

- [ ] Baixar OpenCore mais recente (1.1.x+ ou superior)
- [ ] Substituir `BOOTx64.efi`, `OpenCore.efi`, e drivers em `Drivers/`
- [ ] Usar o novo `Sample.plist` como referência para campos novos
- [ ] Rodar `ocvalidate` para verificar integridade do config.plist

### Fase 3: Atualizar AMD Vanilla Patches

- [ ] Baixar patches atualizados de https://github.com/AMD-OSX/AMD_Vanilla
- [ ] Copiar seção `Kernel → Patch` do patches.plist atualizado
- [ ] Manter o número de cores configurado em 8 (Ryzen 7 4800HS)

### Fase 4: Baixar Recovery e Preparar Pendrive

- [ ] Executar `baixar-macos-recovery.bat` (opção Tahoe) OU comando manual
- [ ] Copiar `com.apple.recovery.boot/` e `EFI/` para pendrive FAT32
- [ ] Pré-configurar Wi-Fi no itlwm (se versão nova ainda suportar injeção direta)

### Fase 5: Boot de Teste (com verbose)

- [ ] Adicionar `-v` aos boot-args temporariamente
- [ ] Boot pelo pendrive → Recovery → Instalar macOS 16
- [ ] Observar logs do verbose para identificar problemas
- [ ] Se parar em algum ponto, fotografar a tela e pesquisar o erro

### Fase 6: Pós-Instalação

- [ ] Instalar HeliPort atualizado (se itlwm ainda funcionar no esquema itlwm + HeliPort)
- [ ] Testar áudio, vídeo, Wi-Fi, teclado, trackpad, bateria, USB
- [ ] Se tudo OK: remover `-v`, copiar EFI para SSD interno
- [ ] Atualizar README.md com nova versão suportada

---

## ⚠️ Plano de Rollback

Se o upgrade falhar em qualquer fase:

1. **Boot pelo pendrive antigo** (com a EFI do Sonoma 14.7)
2. A partição do macOS Sonoma ainda está intacta no SSD
3. O branch `main` no GitHub tem a configuração 100% funcional
4. Clone e restaure: `git checkout main`

---

## 🔗 Referências para o Upgrade

- [AMD_Vanilla Patches (mais recentes)](https://github.com/AMD-OSX/AMD_Vanilla)
- [NootedRed Releases](https://github.com/ChefKissInc/NootedRed/releases)
- [OpenCore Releases](https://github.com/acidanthera/OpenCorePkg/releases)
- [itlwm Releases](https://github.com/OpenIntelWireless/itlwm/releases)
- [Lilu Releases](https://github.com/acidanthera/Lilu/releases)
- [Dortania - Updating OpenCore](https://dortania.github.io/OpenCore-Post-Install/universal/update.html)
- [AMD OS X Discord](https://discord.gg/EfCYAJW) — Canal `#tahoe-support` (verificar)
