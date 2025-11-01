"""Windows Notifications API (Windows-exclusive).

Windows 10+ has a modern notification system that Linux doesn't have
as a unified API. This command sends toast notifications.

Usage:
  notify send "Message"                    # Simple notification
  notify send --title "Alert" "Message"   # With title
  notify send --icon path/to/icon.ico "Message"  # With icon
"""

from __future__ import annotations

import os
import sys
import argparse
from typing import List

if os.name == 'nt':
    try:
        # Try using win10toast for simpler implementation
        from win10toast import ToastNotifier  # type: ignore
        has_toast = True
    except ImportError:
        has_toast = False
        # Fallback to Windows API via ctypes
        try:
            import ctypes
            from ctypes import wintypes
        except ImportError:
            ctypes = None
else:
    has_toast = False
    ctypes = None


def _send_notification(title: str, message: str, icon_path: str = None) -> bool:
    """Send a Windows toast notification. Returns True on success."""
    if os.name != 'nt':
        print('notify: Windows-only feature', file=sys.stderr)
        return False

    if has_toast:
        try:
            toaster = ToastNotifier()
            duration = 5  # seconds
            if icon_path and os.path.exists(icon_path):
                toaster.show_toast(title, message, icon_path=icon_path, duration=duration)
            else:
                toaster.show_toast(title, message, duration=duration)
            return True
        except Exception as e:
            print(f'notify: Failed to send notification: {e}', file=sys.stderr)
            return False
    elif ctypes:
        # Fallback: Use Windows Shell API to show notification
        # This requires Windows 10+ and proper setup
        try:
            # Windows 10+ toast notification via COM
            # Simplified: We'll use a basic message box for now
            user32 = ctypes.windll.user32
            # MB_OK = 0x00000000
            # MB_ICONINFORMATION = 0x00000040
            result = user32.MessageBoxW(
                0,
                message.encode('utf-16le') if isinstance(message, str) else message,
                title.encode('utf-16le') if isinstance(title, str) else title,
                0x00000040  # MB_ICONINFORMATION
            )
            return result != 0
        except Exception as e:
            print(f'notify: Failed to send notification: {e}', file=sys.stderr)
            print('notify: Install win10toast for better notification support: pip install win10toast', file=sys.stderr)
            return False
    else:
        print('notify: Requires win10toast package or Windows API support', file=sys.stderr)
        print('notify: Install with: pip install win10toast', file=sys.stderr)
        return False


def execute(args: List[str]) -> int:
    """Execute the notify command."""
    parser = argparse.ArgumentParser(prog='notify', add_help=False)
    parser.add_argument('action', choices=['send'], nargs='?', help='Action to perform')
    parser.add_argument('message', nargs='*', help='Notification message')
    parser.add_argument('--title', '-t', default='Wilx', help='Notification title')
    parser.add_argument('--icon', '-i', help='Icon path (.ico file)')
    parser.add_argument('-h', '--help', action='store_true', dest='show_help')

    ns = parser.parse_args(args)
    if ns.show_help or not ns.action:
        parser.print_help()
        print()
        print('Examples:')
        print('  notify send "Backup complete"')
        print('  notify send --title "Alert" "Task finished"')
        print('  notify send --icon icon.ico "Message with icon"')
        print('  backup && notify send "Backup successful"')
        return 0

    if ns.action == 'send':
        if not ns.message:
            print('notify: Message required', file=sys.stderr)
            return 1
        
        message_text = ' '.join(ns.message)
        if _send_notification(ns.title, message_text, ns.icon):
            return 0
        else:
            return 1

    return 1

