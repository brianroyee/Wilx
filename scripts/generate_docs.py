"""Generate per-command Markdown docs for Wilx commands in `core/`.

This script discovers modules under `core/` (excluding private files and
`__init__.py`), imports each module, extracts the module docstring, and
captures help text by calling `module.execute(['--help'])` when possible.

Output is written to `docs/commands/<command>.md` with a short header,
module documentation, and the captured help output.

Usage:
    python scripts/generate_docs.py

This tool uses only the standard library so it works in the repo by default.
"""
from __future__ import annotations

import importlib
import io
import contextlib
import os
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / 'core'
OUT_DIR = ROOT / 'docs' / 'commands'

# Ensure the project root is on sys.path so `import core.*` works when running
# this script from the repository root (or any working directory).
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def list_core_modules() -> List[str]:
    out: List[str] = []
    try:
        for p in CORE_DIR.iterdir():
            if p.is_file() and p.suffix == '.py' and not p.name.startswith('_') and p.name != '__init__.py':
                out.append(p.stem)
    except Exception:
        pass
    out.sort()
    return out


def capture_help(module) -> str:
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            try:
                # Many modules accept ['-h'] or ['--help'] — use ['--help'] as convention
                module.execute(['--help'])
            except SystemExit:
                # argparse may call sys.exit after printing help
                pass
            except TypeError:
                # Some modules may not accept execute(args) signature; ignore
                pass
            except Exception:
                # If help invocation fails, ignore and return partial output
                pass
    except Exception:
        return ''
    return buf.getvalue()


def generate():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    modules = list_core_modules()
    if not modules:
        print('No core modules found under core/.')
        return 1

    for name in modules:
        try:
            mod = importlib.import_module(f'core.{name}')
        except Exception as e:
            print(f'Failed to import core.{name}: {e}')
            doc = f'(error importing module: {e})'
            help_text = ''
        else:
            doc = (mod.__doc__ or '').strip()
            help_text = capture_help(mod)

        md_path = OUT_DIR / f'{name}.md'
        try:
            with md_path.open('w', encoding='utf-8') as f:
                f.write(f'# {name}\n\n')
                if doc:
                    f.write('## Description\n\n')
                    f.write(doc + '\n\n')
                else:
                    f.write('*(no module docstring available)*\n\n')

                f.write('## Help\n\n')
                if help_text:
                    f.write("```\n")
                    f.write(help_text.rstrip() + '\n')
                    f.write("```\n")
                else:
                    f.write('*(no help output captured)*\n')
        except Exception as e:
            print(f'Failed to write {md_path}: {e}')
            continue
        print(f'Wrote {md_path}')

    print('\nDocs generated in', OUT_DIR)
    return 0


if __name__ == '__main__':
    sys.exit(generate())
