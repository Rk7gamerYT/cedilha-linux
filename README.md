# Cedilha Linux 🇧🇷

Configure **apóstrofo + c → ç** e **apóstrofo + Shift+C → Ç** em teclados **US internacional com teclas mortas**. Configuração por usuário, sem sudo, independente dos arquivos de instalação dos aplicativos.

> O teclado precisa estar configurado como US internacional **com dead keys**. O script não muda o layout. Em ABNT2, a tecla ç já existe; normalmente você não precisa deste ajuste.

## Instalar

Requer Python 3.8 ou superior e uma sessão Linux de desktop.

```bash
git clone https://github.com/Rk7gamerYT/cedilha-linux.git
cd cedilha-linux
python3 cedilha.py install
```

**Saia da sessão gráfica e entre novamente.** Apenas abrir outro terminal não atualiza os aplicativos já abertos. Teste `ç Ç á é ã` no seu editor e no Discord.

Se GTK/Qt continuarem ignorando a composição e você não depender de IBus/Fcitx:

```bash
python3 cedilha.py uninstall
python3 cedilha.py install --force-input-methods
```

Essa opção força `GTK_IM_MODULE=cedilla` e `QT_IM_MODULE=compose` na próxima sessão e nos Flatpaks. Pode substituir seu método de entrada atual e prejudicar a digitação em idiomas asiáticos; não é o padrão.

## Distribuições

O script usa arquivos de configuração do usuário e não depende do gerenciador de pacotes. Compatibilidade **prevista**, sem testes completos em cada distribuição:

| Família | Exemplos | Instalar Python se necessário |
| --- | --- | --- |
| Debian/Ubuntu | Debian, Ubuntu, Mint, Pop!_OS, Zorin | `sudo apt install python3` |
| Fedora | Fedora Workstation, KDE, Nobara | `sudo dnf install python3` |
| Arch | Arch, EndeavourOS, Manjaro | `sudo pacman -S python` |
| openSUSE | Tumbleweed, Leap | `sudo zypper install python3` |
| Sistemas imutáveis | Silverblue, Kinoite, Bazzite | Use o Python do host, se disponível |

Execute o script **no host, com seu usuário**, não com sudo, em Toolbox/Distrobox ou dentro de um Flatpak. Os comandos de pacotes são referências; o script não instala pacotes.

### Ambientes gráficos

- **KDE Plasma:** adiciona um script de ambiente próprio, além de `environment.d`.
- **GNOME, Cinnamon, Xfce e outros:** usa `environment.d` e um bloco em `~/.profile`. A leitura desses arquivos depende do gerenciador de login e de como o aplicativo é iniciado. Se a sessão não importar essas variáveis, é necessário configurar o ambiente no inicializador da sua sessão.
- **Wayland e X11:** a tabela é usada por aplicativos que suportam Compose/libxkbcommon. Não é uma remarcação de teclas no kernel e não garante suporte em todos os aplicativos, jogos, Snap ou apps com entrada própria.

## Flatpak

Se `flatpak` estiver instalado, aplica um override global **do seu usuário** para aplicativos atuais e futuros. Compartilha somente `~/.XCompose` em leitura e define `XCOMPOSEFILE`. Não concede acesso a toda a pasta pessoal. Overrides específicos de um aplicativo podem prevalecer.

```bash
# Pular configuração Flatpak
python3 cedilha.py install --no-flatpak

# Conferir as configurações globais
flatpak override --user --show
```

Se instalar o Flatpak depois, desinstale a configuração deste script e instale novamente. Inclusões personalizadas do seu `.XCompose` podem precisar de permissões próprias dentro do sandbox.

## O que muda

- Acrescenta as duas regras ao `.XCompose`, preservando o conteúdo anterior; em arquivo novo, inclui primeiro a tabela padrão `%L`.
- Cria `99-cedilha-linux.conf` em `$XDG_CONFIG_HOME/environment.d`.
- Cria `99-cedilha-linux.sh` em `$XDG_CONFIG_HOME/plasma-workspace/env`.
- Acrescenta um bloco ao `~/.profile`.
- Quando disponível, atualiza o override global Flatpak, preservando as outras opções.

Não altera locale, layout, atalhos do sistema ou arquivos dos pacotes. Não modifica os processos já abertos. Repetir a instalação não duplica regras; para trocar opções, desinstale primeiro.

## Verificar e desfazer

```bash
python3 cedilha.py status
python3 cedilha.py uninstall
```

O backup fica em `$XDG_STATE_HOME/cedilha-linux/backup.json` (padrão `~/.local/state/cedilha-linux/backup.json`). Ele contém os arquivos anteriores, inclusive `.profile`; mantenha-o privado e não o envie para issues.

A reversão restaura os arquivos anteriores. Se algum arquivo mudou após a instalação, **recusa a reversão inteira**, para não apagar novas configurações. Isso inclui mudanças feitas pelo Flatseal no override global. Nesse caso, use o backup para restaurar manualmente apenas o necessário. Uma interrupção abrupta durante a instalação também pode exigir restauração manual. Após desfazer, saia e entre na sessão.

## Validação

```bash
python3 -m unittest discover -v
```

Os testes usam diretórios temporários e verificam preservação, instalação repetida, reversão, proteção de edições posteriores, opção de métodos de entrada e rollback quando Flatpak falha. Não iniciam aplicativos gráficos. A configuração Compose e a leitura pelo sandbox Flatpak foram verificadas no computador de origem, KDE/Wayland; não há certificação de todas as distros ou apps.

## Referências

- [libxkbcommon: Compose e dead keys](https://xkbcommon.org/doc/current/group__compose.html)
- [Flatpak: referência dos comandos e overrides](https://docs.flatpak.org/en/latest/flatpak-command-reference.html)

## Licença

MIT — veja [LICENSE](LICENSE).
