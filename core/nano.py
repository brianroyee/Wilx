"""Tiny nano-like text editor for Wilx.

Behavior:
- If the environment has `curses`, launches a simple full-screen editor with:
  - Arrow key navigation, Insert/Delete, Enter
  - Ctrl-S to save, Ctrl-Q to quit (unsaved changes prompt)
- If `curses` isn't available (common on Windows without packages), falls back to
  a simple line-based editor that lets you view, append, delete lines, and save.

This is intentionally minimal — it's not a full nano clone, but provides an
easy-to-use in-terminal editing experience without external dependencies.
"""
from __future__ import annotations

import os
import sys
import argparse
import time
from typing import List


def _usage():
    return "Usage: nano [filename] — Ctrl-S save, Ctrl-Q quit (in curses mode)"


def _append_history(history_file: str | None, path: str) -> None:
    if not history_file:
        return
    try:
        p = os.path.expanduser(history_file)
        d = os.path.dirname(p)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(p, 'a', encoding='utf-8') as f:
            f.write(f"{int(time.time())}\t{path}\n")
    except Exception:
        pass


def _run_line_editor(path: str, show_line_numbers: bool = False, history_file: str | None = None) -> int:
    # Very simple fallback: show lines, allow commands to edit.
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [ln.rstrip('\n') for ln in f]
    else:
        lines = []

    print('Simple nano fallback — line editor')
    print('Commands: i <n> (insert before n), a (append), d <n> (delete), p (print), w (write), q (quit)')
    while True:
        cmd = input('> ').strip()
        if not cmd:
            continue
        if cmd == 'p':
            for i, ln in enumerate(lines, 1):
                if show_line_numbers:
                    print(f'{i:6d}  {ln}')
                else:
                    print(f'{i:4d}: {ln}')
            continue
        if cmd.startswith('i '):
            try:
                n = int(cmd.split(None, 1)[1])
            except Exception:
                print('invalid line number')
                continue
            text = input('insert> ')
            idx = max(0, min(len(lines), n - 1))
            lines.insert(idx, text)
            continue
        if cmd == 'a':
            text = input('append> ')
            lines.append(text)
            continue
        if cmd.startswith('d '):
            try:
                n = int(cmd.split(None, 1)[1])
                idx = n - 1
                if 0 <= idx < len(lines):
                    lines.pop(idx)
                else:
                    print('invalid line number')
            except Exception:
                print('invalid command')
            continue
        if cmd == 'w':
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    for ln in lines:
                        f.write(ln + '\n')
                print('Wrote', path)
                # record to history when writing
                try:
                    _append_history(history_file, path)
                except Exception:
                    pass
            except Exception as e:
                print('write failed:', e)
            continue
        if cmd in ('q', 'quit'):
            return 0
        print('unknown command')


def _run_curses_editor(path: str, show_line_numbers: bool = False, history_file: str | None = None) -> int:
    import curses

    def _save(buf_lines: List[str], fname: str = None):
        target = fname or path
        with open(target, 'w', encoding='utf-8') as f:
            for ln in buf_lines:
                f.write(ln + '\n')


    def _main(stdscr):
        curses.curs_set(1)
        stdscr.keypad(True)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                buf = [ln.rstrip('\n') for ln in f]
        else:
            buf = ['']

        y = x = 0
        top = 0
        changed = False

        undo_stack: List[List[str]] = []
        MAX_UNDO = 50

        def push_undo():
            if len(undo_stack) >= MAX_UNDO:
                undo_stack.pop(0)
            undo_stack.append(list(buf))

        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            visible = buf[top:top + h - 1]
            for i, line in enumerate(visible):
                if show_line_numbers:
                    num = f"{top + i + 1:6d}  "
                    # ensure we don't overflow width
                    avail = max(0, w - len(num) - 1)
                    stdscr.addstr(i, 0, num + line[:avail])
                else:
                    stdscr.addstr(i, 0, line[:w - 1])
            status = f"{path} - Ctrl-S save | Ctrl-Q quit | Ln {top + y + 1},Col {x + 1}"
            stdscr.addstr(h - 1, 0, status[:w - 1], curses.A_REVERSE)
            stdscr.move(y, x)
            stdscr.refresh()
            ch = stdscr.getch()
            if ch == curses.KEY_DOWN:
                if y + top + 1 < len(buf):
                    if y < h - 2:
                        y += 1
                    else:
                        top += 1
                    x = min(x, len(buf[top + y]))
            elif ch == curses.KEY_UP:
                if y > 0:
                    y -= 1
                elif top > 0:
                    top -= 1
                x = min(x, len(buf[top + y]))
            elif ch == curses.KEY_LEFT:
                if x > 0:
                    x -= 1
            elif ch == curses.KEY_RIGHT:
                if x < len(buf[top + y]):
                    x += 1
            # Backspace: handle several possible codes (127, 8, KEY_BACKSPACE) and curses.ascii.BS
            elif ch in (127, 8, curses.KEY_BACKSPACE) or (hasattr(curses, 'ascii') and ch == curses.ascii.BS):
                line = buf[top + y]
                if x > 0:
                    buf[top + y] = line[:x - 1] + line[x:]
                    x -= 1
                    changed = True
                elif x == 0 and (top + y) > 0:
                    prev = buf.pop(top + y)
                    y = max(0, y - 1)
                    buf[top + y] = buf[top + y] + prev
                    changed = True
            elif ch == 19:  # Ctrl-S
                try:
                    _save(buf)
                    changed = False
                    # record to history on save
                    try:
                        _append_history(history_file, path)
                    except Exception:
                        pass
                except Exception as e:
                    stdscr.addstr(h - 2, 0, f'Save failed: {e}')
                    stdscr.getch()
            elif ch == 17:  # Ctrl-Q
                if changed:
                    stdscr.addstr(h - 2, 0, 'Unsaved changes - press Ctrl-Q again to quit without saving')
                    stdscr.refresh()
                    c2 = stdscr.getch()
                    if c2 == 17:
                        return
                else:
                    return
            elif ch == curses.KEY_ENTER or ch == 10:
                line = buf[top + y]
                rest = line[x:]
                push_undo()
                buf[top + y] = line[:x]
                buf.insert(top + y + 1, rest)
                y = min(y + 1, h - 2)
                x = 0
                changed = True
            elif 0 <= ch < 256:
                push_undo()
                line = buf[top + y]
                buf[top + y] = line[:x] + chr(ch) + line[x:]
                x += 1
                changed = True
            elif ch == 15:  # Ctrl-O (save as)
                # prompt for filename in status line
                curses.echo()
                stdscr.addstr(h - 2, 0, 'Save as: ')
                stdscr.clrtoeol()
                stdscr.refresh()
                fname = stdscr.getstr(h - 2, 9, 200).decode(errors='ignore')
                curses.noecho()
                if fname:
                    try:
                        _save(buf, fname)
                        stdscr.addstr(h - 2, 0, f'Saved as {fname}')
                        stdscr.getch()
                        changed = False
                    except Exception as e:
                        stdscr.addstr(h - 2, 0, f'Save failed: {e}')
                        stdscr.getch()
            elif ch == 6:  # Ctrl-F search
                curses.echo()
                stdscr.addstr(h - 2, 0, 'Search: ')
                stdscr.clrtoeol()
                stdscr.refresh()
                query = stdscr.getstr(h - 2, 8, 200).decode(errors='ignore')
                curses.noecho()
                if query:
                    found = False
                    for i, ln in enumerate(buf):
                        if query in ln:
                            # jump to first match
                            if i >= top + h - 1:
                                top = max(0, i - (h // 2))
                                y = i - top
                            else:
                                y = i - top
                            x = ln.find(query)
                            found = True
                            break
                    if not found:
                        stdscr.addstr(h - 2, 0, f'Not found: {query}')
                        stdscr.getch()
            elif ch == 21:  # Ctrl-U undo
                if undo_stack:
                    last = undo_stack.pop()
                    buf[:] = last
                    changed = True

    try:
        import curses
        curses.wrapper(_main)
        return 0
    except Exception as e:
        print('curses editor failed:', e)
        return 1


def execute(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog='nano')
    parser.add_argument('file', nargs='?', help='file to edit')
    parser.add_argument('--line-numbers', action='store_true', help='show line numbers (gutter)')
    parser.add_argument('--history-file', help='path to history file to record saves (default ~/.wilx_history)')
    ns = parser.parse_args(argv)
    path = ns.file or 'untitled.txt'

    history_file = ns.history_file or os.path.expanduser('~/.wilx_history')

    # Try curses editor first, fallback to line editor
    try:
        import curses
        return _run_curses_editor(path, show_line_numbers=ns.line_numbers, history_file=history_file)
    except Exception:
        return _run_line_editor(path, show_line_numbers=ns.line_numbers, history_file=history_file)


if __name__ == '__main__':
    sys.exit(execute(sys.argv[1:]))
