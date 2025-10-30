import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import shell as s

tests = [r'.\\', r'.\\script.py', r'ls -l', r'echo "a b"', r'C:\\Program Files\\app.exe arg']

print('parsing tests:')
for t in tests:
    try:
        parsed = s.parse_command(t)
        print('IN:', t, '->', parsed)
    except Exception as e:
        print('IN:', t, '-> error', e)
