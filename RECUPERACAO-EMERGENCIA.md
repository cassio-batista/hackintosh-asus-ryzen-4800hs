# 🚨 Guia de Recuperação de Emergência

> **Situação**: macOS 26 (Tahoe) atualizado mas não inicia mais.
> **Sintomas**: Barra de progresso chega à metade → reinicia. Pendrive com EFI Sonoma mostra ícone de bloqueio.
> **Boas novas**: Recovery do HD abre normalmente → macOS está intacto, só o bootloader/kexts precisam ser atualizados.

---

## 🔬 Diagnóstico Técnico

### Por que está falhando?

O macOS foi atualizado de **Sonoma (kernel 23.x)** para **Tahoe (kernel 25.x)**. A EFI no SSD e no pendrive ainda tem kexts compilados para o kernel antigo. O resultado é:

1. **Boot loop no progresso** = Kernel Panic causado por kexts incompatíveis com kernel 25.x. O principal suspeito é o **NootedRed** (driver da iGPU). Semelhante a rodar um `.app` construído para uma versão mais antiga — simplesmente trava.

2. **Ícone de bloqueio no pendrive** = OpenCore 1.0.4 (Sonoma-era) não consegue verificar e inicializar o volume APFS do Tahoe. É uma barreira de versão do bootloader, não do macOS em si.

3. **Recovery funciona** = O ambiente de Recovery usa um kernel/drivers próprios embutidos no disco, independentes da EFI. Por isso abre. O macOS instalado está íntegro.

### Estrutura de versões de kernel

| macOS | Kernel Darwin |
|---|---|
| Sonoma 14.x | 23.x |
| Sequoia 15.x | 24.x |
| **Tahoe 26.x** | **25.x** ← você está aqui |

---

## 🛠️ Plano de Recuperação (Ordem Obrigatória)

### FASE 1 — Preparar a EFI Tahoe no Windows (este computador)

> Todos os passos abaixo são no Windows, na pasta do projeto.

#### Passo 1.1 — Baixar kexts atualizados

```powershell
cd "C:\Users\cassi\git\New folder"
python baixar-kexts-tahoe.py
```

O script baixa automaticamente a versão mais recente de cada kext do GitHub.

**⚠️ ATENÇÃO ANTES DE AVANÇAR:**
- Quando o script baixar o **NootedRed**, verifique se a release tem menção a "macOS 26", "Tahoe" ou "kernel 25". Se a versão baixada for igual ou menor que `0.8.3`, o projeto ainda não tem suporte a Tahoe.
- **Se NootedRed não suportar Tahoe ainda**: veja a seção "Fallback" no final deste guia.

#### Passo 1.2 — Copiar kexts para a EFI

Quando o script terminar e confirmar que NootedRed + itlwm têm versão compatível:

```powershell
python baixar-kexts-tahoe.py --copy
```

Isso substitui os kexts em `efi_macos/EFI/OC/Kexts/` pelas versões novas.

#### Passo 1.3 — Verificar o config.plist

O `config.plist` nesta branch já foi atualizado com:
- ✅ `-v debug=0x100` nos boot-args (verbose + panic log)
- ✅ `AppleDebug = True` e `ApplePanic = True`
- ✅ `DisableSecurityPolicy = True` (necessário para Tahoe)

Você não precisa editar o config.plist manualmente.

#### Passo 1.4 — Copiar EFI para o pendrive

```powershell
python copiar-efi-para-pendrive.py
```

Certifique-se de que o pendrive está em `U:` (FAT32). O script copia `efi_macos/EFI/` para ele.

> **Não precisa** da pasta `com.apple.recovery.boot` no pendrive desta vez — você não está instalando, apenas bootando o macOS que já está no SSD.

---

### FASE 2 — Boot pelo Pendrive e Diagnóstico

#### Passo 2.1 — Configurar BIOS

1. Ligue o notebook e entre na BIOS (F2 no boot da ASUS).
2. Coloque o pendrive USB como **primeiro dispositivo de boot**.
3. Garanta que `Secure Boot` está **desabilitado**.
4. Salve e reinicie.

#### Passo 2.2 — Selecionar a entrada correta no OpenCore

No picker do OpenCore, você verá algo como:
- `macOS` (a instalação no SSD)
- `Reset NVRAM`

**Selecione `macOS`.** Se não aparecer nada útil, selecione `Reset NVRAM` primeiro, reinicie, e tente de novo.

#### Passo 2.3 — Observar o boot verbose

Com `-v` ativado, você verá o texto completo do boot. Observe onde para:

| Onde para | Causa provável |
|---|---|
| `Still waiting for root device` | USB/NVMe não montando |
| `[IGPU]` ou `[GFX0]` ou mensagem de GPU | NootedRed incompatível com kernel 25.x |
| `Lilu FIXME` ou `Lilu: kext X not loaded` | Lilu ou kext dependente incompatível |
| `itlwm: ...` ou `IntelBT: ...` | Wi-Fi/BT kext incompatível |
| `AMFIPass: ...` | AMFIPass incompatível |
| Kernel Panic com backtrace | Veja o módulo no topo do backtrace |

**Fotografe a tela** se o boot travar — o texto identifica exatamente qual kext está causando o problema.

---

### FASE 3 — Se o Boot Funcionar

1. Acesse o macOS normalmente.
2. Abra o Terminal e monte a EFI do SSD:
   ```bash
   diskutil list
   sudo diskutil mount disk0s1
   ```
3. Abra o Finder — a partição "EFI" aparecerá.
4. Copie a pasta `EFI/` do pendrive para substituir a do SSD.
5. Reinicie **sem o pendrive** para confirmar que o SSD boota sozinho.
6. Remova `-v debug=0x100` dos boot-args (via ProperTree ou `check-config.py`).

---

### FASE 4 — Se o Boot Ainda Falhar (por causa do NootedRed)

#### Opção A: Desabilitar NootedRed temporariamente (tela preta, mas sistema funciona)

Se NootedRed ainda não suporta Tahoe, desabilite-o no config.plist:

```xml
<!-- No Kexts → NootedRed.kext → Enabled -->
<false/>
```

Sem NootedRed:
- ❌ Sem aceleração gráfica (tela lenta/pixelada)
- ✅ Sistema funciona para uso mínimo (Terminal, SSH, etc.)
- ✅ Permite fazer o boot e copiar a EFI para o SSD

#### Opção B: Rollback para Sonoma

Se o Tahoe estiver irrecuperável:

**No Recovery (que você já sabe acessar):**
1. Abra Terminal no Recovery.
2. Reinstale macOS Sonoma a partir do Recovery ou de um pendrive com Sonoma recovery.
3. Use a configuração de `main` deste repositório.

```powershell
# No Windows, voltar para a EFI do Sonoma:
git checkout main
python copiar-efi-para-pendrive.py
# Depois reinstalar Sonoma pelo pendrive com recovery
```

---

## 📋 Checklist de Progresso

- [ ] Script `baixar-kexts-tahoe.py` rodou com sucesso
- [ ] NootedRed nova versão confirmada (> 0.8.3 com suporte Tahoe)
- [ ] itlwm nova versão confirmada (> 2.3.0 com suporte Tahoe)
- [ ] EFI copiada para o pendrive
- [ ] Boot verbose funciona (sem travar no logo)
- [ ] macOS 26 inicializando normalmente
- [ ] EFI copiada para o SSD interno
- [ ] Boot sem pendrive confirmado
- [ ] `-v debug=0x100` removido dos boot-args

---

## 🔗 Links Úteis para Verificar Compatibilidade

- **NootedRed** (GPU AMD — crítico): https://github.com/ChefKissInc/NootedRed/releases
- **itlwm** (Wi-Fi Intel): https://github.com/OpenIntelWireless/itlwm/releases
- **Lilu**: https://github.com/acidanthera/Lilu/releases
- **AMD Vanilla Patches**: https://github.com/AMD-OSX/AMD_Vanilla
- **OpenCore** (se precisar atualizar o bootloader): https://github.com/acidanthera/OpenCorePkg/releases
- **AMD OS X Discord**: https://discord.gg/EfCYAJW — canal #tahoe ou #nootedred-support

---

## ⚡ TL;DR — Resumo de 3 linhas

1. Rode `python baixar-kexts-tahoe.py` no Windows para baixar kexts Tahoe.
2. Copie para o pendrive com `python baixar-kexts-tahoe.py --copy && python copiar-efi-para-pendrive.py`.
3. Boot pelo pendrive → se funcionar, copie a EFI do pendrive para o SSD.
