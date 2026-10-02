#!/usr/bin/env python3
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import zipfile
ROOT = Path(__file__).resolve().parents[1]

def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: package.py /absolute/path/output.zip')
    output = Path(sys.argv[1])
    if not output.is_absolute() or output.suffix != '.zip':
        raise SystemExit('Output must be an absolute .zip path.')
    output.parent.mkdir(parents=True, exist_ok=True)
    names = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z']).decode().split('\0')
    files = sorted(name for name in names if name)
    if not files:
        raise SystemExit('No tracked files; add the package files to Git first.')
    for name in files:
        path = ROOT / name
        if not path.is_file() or path.is_symlink():
            raise SystemExit('Expected a regular tracked file: ' + name)
        if output == path.resolve():
            raise SystemExit('Output cannot replace a source file.')
    fd, temporary = tempfile.mkstemp(prefix='.mac-dev-zip-', dir=output.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name in files:
                archive.write(ROOT / name, ROOT.name + '/' + name)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise SystemExit('ZIP integrity check failed.')
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(output)

if __name__ == '__main__':
    main()
