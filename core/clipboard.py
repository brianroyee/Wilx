"""Windows Clipboard Integration (Windows-exclusive).

This command provides clipboard operations that are unique to Windows.
Linux has fragmented clipboard systems, while Windows has a unified API.

Usage:
  clipboard copy <text>      # Copy text to clipboard
  clipboard paste            # Paste clipboard to stdout
  clipboard show             # Display clipboard contents
  clipboard clear            # Clear clipboard

The clipboard can also be used in pipes:
  pwd | clipboard copy       # Copy current directory to clipboard
  echo "Hello" | clipboard copy
  clipboard paste > file.txt
"""

from __future__ import annotations

import os
import sys
import argparse
from typing import List

if os.name == 'nt':
    try:
        import win32clipboard  # type: ignore
    except ImportError:
        win32clipboard = None
        # Fallback to ctypes for pure Python solution
        try:
            import ctypes
            from ctypes import wintypes
        except ImportError:
            ctypes = None
else:
    win32clipboard = None
    ctypes = None


def _copy_to_clipboard(text: str) -> bool:
    """Copy text to Windows clipboard. Returns True on success."""
    if os.name != 'nt':
        print('clipboard: Windows-only feature', file=sys.stderr)
        return False

    if win32clipboard:
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text)
            win32clipboard.CloseClipboard()
            return True
        except Exception:
            return False
    elif ctypes:
        # Pure Python fallback using ctypes
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            # CF_UNICODETEXT = 13
            CF_UNICODETEXT = 13

            user32.OpenClipboard(None)
            user32.EmptyClipboard()

            # Allocate and copy text
            text_bytes = text.encode('utf-16le')
            hmem = kernel32.GlobalAlloc(0x2000, len(text_bytes) + 2)  # GMEM_MOVEABLE
            mem = kernel32.GlobalLock(hmem)
            ctypes.memmove(mem, text_bytes, len(text_bytes))
            kernel32.GlobalUnlock(hmem)

            user32.SetClipboardData(CF_UNICODETEXT, hmem)
            user32.CloseClipboard()
            return True
        except Exception:
            try:
                user32.CloseClipboard()
            except Exception:
                pass
            return False
    else:
        print('clipboard: Requires win32clipboard package or ctypes support', file=sys.stderr)
        return False


def _get_clipboard_text() -> str | None:
    """Get text from Windows clipboard. Returns None on failure."""
    if os.name != 'nt':
        print('clipboard: Windows-only feature', file=sys.stderr)
        return None

    if win32clipboard:
        try:
            win32clipboard.OpenClipboard()
            try:
                text = win32clipboard.GetClipboardData()
            except Exception:
                text = None
            win32clipboard.CloseClipboard()
            return text if isinstance(text, str) else None
        except Exception:
            return None
    elif ctypes:
        # Pure Python fallback using ctypes
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            CF_UNICODETEXT = 13

            user32.OpenClipboard(None)
            hmem = user32.GetClipboardData(CF_UNICODETEXT)
            if not hmem:
                user32.CloseClipboard()
                return None

            mem = kernel32.GlobalLock(hmem)
            if not mem:
                user32.CloseClipboard()
                return None

            # Get size first
            size = kernel32.GlobalSize(hmem)
            buffer = ctypes.create_unicode_buffer(size // 2)
            ctypes.memmove(buffer, mem, size)
            kernel32.GlobalUnlock(hmem)
            user32.CloseClipboard()

            # Remove null terminator
            text = buffer.value.rstrip('\x00')
            return text
        except Exception:
            try:
                user32.CloseClipboard()
            except Exception:
                pass
            return None
    else:
        print('clipboard: Requires win32clipboard package or ctypes support', file=sys.stderr)
        return None


def _clear_clipboard() -> bool:
    """Clear the Windows clipboard. Returns True on success."""
    if os.name != 'nt':
        print('clipboard: Windows-only feature', file=sys.stderr)
        return False

    if win32clipboard:
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
            return True
        except Exception:
            return False
    elif ctypes:
        try:
            user32 = ctypes.windll.user32
            user32.OpenClipboard(None)
            user32.EmptyClipboard()
            user32.CloseClipboard()
            return True
        except Exception:
            try:
                user32.CloseClipboard()
            except Exception:
                pass
            return False
    else:
        print('clipboard: Requires win32clipboard package or ctypes support', file=sys.stderr)
        return False


def execute(args: List[str]) -> int:
    """Execute the clipboard command."""
    parser = argparse.ArgumentParser(prog='clipboard', add_help=False)
    parser.add_argument('action', choices=['copy', 'paste', 'show', 'clear'], nargs='?', help='Action to perform')
    parser.add_argument('text', nargs='*', help='Text to copy (for copy action)')
    parser.add_argument('-h', '--help', action='store_true', dest='show_help')

    ns = parser.parse_args(args)
    if ns.show_help or not ns.action:
        parser.print_help()
        print()
        print('Examples:')
        print('  clipboard copy "Hello World"')
        print('  clipboard paste')
        print('  pwd | clipboard copy')
        print('  clipboard show')
        print('  clipboard clear')
        return 0

    if ns.action == 'copy':
        if ns.text:
            # Copy text from arguments
            text = ' '.join(ns.text)
        else:
            # Read from stdin
            text = sys.stdin.read()
            if not text:
                print('clipboard: No text provided', file=sys.stderr)
                return 1

        if _copy_to_clipboard(text):
            return 0
        else:
            print('clipboard: Failed to copy to clipboard', file=sys.stderr)
            return 1

    elif ns.action == 'paste' or ns.action == 'show':
        text = _get_clipboard_text()
        if text is None:
            print('clipboard: Failed to read clipboard or clipboard is empty', file=sys.stderr)
            return 1
        print(text, end='')
        return 0

    elif ns.action == 'clear':
        if _clear_clipboard():
            return 0
        else:
            print('clipboard: Failed to clear clipboard', file=sys.stderr)
            return 1

    return 1

