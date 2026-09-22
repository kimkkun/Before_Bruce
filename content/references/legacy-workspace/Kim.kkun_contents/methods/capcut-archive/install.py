#!/usr/bin/python3
"""Install this checkout's read-only export collector as a per-user LaunchAgent."""
import os
import plistlib
import subprocess
from pathlib import Path

if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    support = here.parents[2] / '김꾼_영상보관' / '99_관리자료' / '자동보관'
    support.mkdir(parents=True, exist_ok=True)
    label = 'com.kimkkun.capcut-export-archive'
    domain = 'gui/' + str(os.getuid())
    target = Path.home() / 'Library/LaunchAgents' / (label + '.plist')
    target.parent.mkdir(parents=True, exist_ok=True)
    config = {'Label': label, 'ProgramArguments': ['/usr/bin/python3', str(here / 'archive_exports.py')],
              'RunAtLoad': True, 'StartInterval': 60, 'ProcessType': 'Background',
              'StandardOutPath': str(support / 'service.log'), 'StandardErrorPath': str(support / 'service-error.log')}
    active = subprocess.run(['launchctl', 'print', domain + '/' + label], capture_output=True).returncode == 0
    if active:
        subprocess.run(['launchctl', 'bootout', domain + '/' + label], check=True)
    target.write_bytes(plistlib.dumps(config))
    subprocess.run(['launchctl', 'bootstrap', domain, str(target)], check=True)
    subprocess.run(['launchctl', 'print', domain + '/' + label], check=True)
