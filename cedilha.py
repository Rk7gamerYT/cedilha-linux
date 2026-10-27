#!/usr/bin/env python3
"""Cedilha para teclado US internacional. Sem sudo; somente biblioteca padrão."""
import argparse
import base64
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['install', 'status', 'uninstall'])
    p.add_argument('--no-flatpak', action='store_true')
    p.add_argument('--force-input-methods', action='store_true',
                   help='Força GTK cedilla e Qt compose; pode substituir IBus/Fcitx.')
    a = p.parse_args()
    if sys.platform != 'linux' or os.geteuid() == 0:
        p.error('Execute no Linux como usuário normal, sem sudo.')
    home = Path.home()
    config = Path(os.environ.get('XDG_CONFIG_HOME', home / '.config'))
    data = Path(os.environ.get('XDG_DATA_HOME', home / '.local/share'))
    state = Path(os.environ.get('XDG_STATE_HOME', home / '.local/state')) / 'cedilha-linux'
    manifest = state / 'backup.json'
    if a.action == 'status':
        print('Instalado.' if manifest.exists() else 'Não instalado por este script.')
        print('Desktop:', os.environ.get('XDG_CURRENT_DESKTOP', 'desconhecido'))
        print('Sessão:', os.environ.get('XDG_SESSION_TYPE', 'desconhecida'))
        print('XCOMPOSEFILE da sessão:', os.environ.get('XCOMPOSEFILE', '(não definido)'))
        return

    def snapshot(path):
        if path.is_symlink():
            raise RuntimeError(f'Link simbólico não será alterado: {path}')
        return None if not path.exists() else base64.b64encode(path.read_bytes()).decode()

    def restore(records):
        for name, item in records.items():
            path = Path(name)
            if item['before'] is None:
                path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(base64.b64decode(item['before']))
                path.chmod(item['mode'])

    if a.action == 'uninstall':
        if not manifest.exists():
            print('Nada para desfazer.')
            return
        records = json.loads(manifest.read_text())
        for name, item in records.items():
            if 'after' not in item:
                raise RuntimeError(f'Instalação interrompida. Restaure manualmente usando {manifest}.')
            if snapshot(Path(name)) != item['after']:
                raise RuntimeError(f'Arquivo modificado depois da instalação: {name}. '
                                   f'Restaure manualmente usando {manifest}; nenhum arquivo foi alterado.')
        restore(records)
        manifest.unlink()
        print('Configuração anterior restaurada. Saia e entre na sessão.')
        return
    if manifest.exists():
        print('Já instalado. Para mudar opções, execute uninstall e depois install.')
        return
    if not str(config).startswith('/') or not str(data).startswith('/'):
        raise RuntimeError('XDG_CONFIG_HOME e XDG_DATA_HOME devem ser caminhos absolutos.')
    compose = home / '.XCompose'
    env = {'XCOMPOSEFILE': str(compose)}
    if a.force_input_methods:
        env.update(GTK_IM_MODULE='cedilla', QT_IM_MODULE='compose')
    # environment.d tem sua própria sintaxe, diferente de shell.
    def env_quote(value):
        if any(ch in value for ch in '\n\r$`'):
            raise RuntimeError('Caminho não suportado pela configuração environment.d.')
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
    exports = '\n'.join(f'export {k}={shlex.quote(v)}' for k, v in env.items()) + '\n'
    original = compose.read_text() if compose.exists() else 'include "%L"\n'
    rules = ('\n# BEGIN cedilha-linux\n'
             '<dead_acute> <c> : "ç" ccedilla\n'
             '<dead_acute> <C> : "Ç" Ccedilla\n'
             '# END cedilha-linux\n')
    profile = home / '.profile'
    profile_text = profile.read_text() if profile.exists() else ''
    files = {
        compose: original + rules,
        config / 'environment.d/99-cedilha-linux.conf':
            '\n'.join(f'{k}={env_quote(v)}' for k, v in env.items()) + '\n',
        config / 'plasma-workspace/env/99-cedilha-linux.sh': '#!/bin/sh\n' + exports,
        profile: profile_text + '\n# BEGIN cedilha-linux\n' + exports + '# END cedilha-linux\n',
    }
    flatpak = shutil.which('flatpak') if not a.no_flatpak else None
    global_override = data / 'flatpak/overrides/global'
    paths = list(files) + ([global_override] if flatpak else [])
    records = {str(path): {'before': snapshot(path),
                           'mode': path.stat().st_mode & 0o777 if path.exists() else 0o644}
               for path in paths}
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Guarda o backup antes de qualquer alteração, inclusive em caso de interrupção.
    def save():
        manifest.write_text(json.dumps(records, indent=2))
        manifest.chmod(0o600)
    save()
    try:
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        if flatpak:
            subprocess.run([flatpak, 'override', '--user',
                            f'--filesystem={compose}:ro',
                            *[f'--env={k}={v}' for k, v in env.items()]], check=True)
        for name, item in records.items():
            item['after'] = snapshot(Path(name))
        save()
    except BaseException:
        restore(records)
        manifest.unlink(missing_ok=True)
        raise
    print('Instalado. Saia e entre novamente na sessão gráfica.')
    print('Flatpak:', 'configurado para apps atuais e futuros.' if flatpak else 'não alterado.')
    print('Teste: apóstrofo + c → ç; apóstrofo + Shift+C → Ç.')
    print('Backup:', manifest)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(f'Erro: {error}')
