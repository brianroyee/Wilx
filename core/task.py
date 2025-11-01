"""Windows Task Scheduler Integration (Windows-exclusive).

Windows Task Scheduler is native and easier to use than Linux cron.
This command provides a simple interface to schedule tasks.

Usage:
  task schedule add cleanup "rm -rf ~/tmp/*" "daily 2am"
  task schedule list
  task schedule remove cleanup
  task schedule run cleanup
"""

from __future__ import annotations

import os
import sys
import argparse
import subprocess
from typing import List
import re


def _parse_schedule(schedule_str: str) -> dict:
    """Parse human-readable schedule string into task scheduler format.
    
    Examples:
      "daily 2am" -> daily at 2am
      "weekly sunday 3am" -> weekly on Sunday at 3am
      "monthly 1st 1am" -> monthly on 1st at 1am
    """
    schedule = {}
    schedule_str = schedule_str.lower().strip()
    
    # Daily
    daily_match = re.match(r'daily\s+(\d+)(am|pm)', schedule_str)
    if daily_match:
        hour = int(daily_match.group(1))
        period = daily_match.group(2)
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        schedule['type'] = 'daily'
        schedule['time'] = f'{hour:02d}:00'
        return schedule
    
    # Weekly
    weekly_match = re.match(r'weekly\s+(\w+)\s+(\d+)(am|pm)', schedule_str)
    if weekly_match:
        day = weekly_match.group(1)
        hour = int(weekly_match.group(2))
        period = weekly_match.group(3)
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        schedule['type'] = 'weekly'
        schedule['day'] = day
        schedule['time'] = f'{hour:02d}:00'
        return schedule
    
    # Monthly
    monthly_match = re.match(r'monthly\s+(\d+)(st|nd|rd|th)\s+(\d+)(am|pm)', schedule_str)
    if monthly_match:
        day_num = int(monthly_match.group(1))
        hour = int(monthly_match.group(3))
        period = monthly_match.group(4)
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        schedule['type'] = 'monthly'
        schedule['day'] = day_num
        schedule['time'] = f'{hour:02d}:00'
        return schedule
    
    # Simple time format: HH:MM
    time_match = re.match(r'(\d{1,2}):(\d{2})', schedule_str)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        schedule['type'] = 'daily'
        schedule['time'] = f'{hour:02d}:{minute:02d}'
        return schedule
    
    # Default: daily at specified time
    return {'type': 'daily', 'time': '00:00'}


def _schedule_task(name: str, command: str, schedule_str: str) -> bool:
    """Schedule a task using Windows Task Scheduler."""
    if os.name != 'nt':
        print('task: Windows-only feature', file=sys.stderr)
        return False
    
    schedule = _parse_schedule(schedule_str)
    
    try:
        # Use schtasks.exe to create task
        # Build schtasks command
        cmd_parts = ['schtasks', '/Create', '/TN', name, '/TR', command, '/SC']
        
        if schedule['type'] == 'daily':
            cmd_parts.extend(['DAILY', '/ST', schedule['time']])
        elif schedule['type'] == 'weekly':
            day_map = {
                'sunday': 'SU', 'monday': 'MO', 'tuesday': 'TU',
                'wednesday': 'WE', 'thursday': 'TH', 'friday': 'FR', 'saturday': 'SA'
            }
            day_abbr = day_map.get(schedule.get('day', '').lower(), 'SU')
            cmd_parts.extend(['WEEKLY', '/D', day_abbr, '/ST', schedule['time']])
        elif schedule['type'] == 'monthly':
            cmd_parts.extend(['MONTHLY', '/D', str(schedule.get('day', 1)), '/ST', schedule['time']])
        else:
            cmd_parts.extend(['DAILY', '/ST', schedule['time']])
        
        # Run without prompting
        cmd_parts.append('/F')
        
        result = subprocess.run(cmd_parts, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f'task: Scheduled task "{name}" successfully')
            return True
        else:
            print(f'task: Failed to schedule task: {result.stderr}', file=sys.stderr)
            return False
    except Exception as e:
        print(f'task: Error scheduling task: {e}', file=sys.stderr)
        return False


def _list_tasks() -> bool:
    """List all scheduled tasks."""
    if os.name != 'nt':
        print('task: Windows-only feature', file=sys.stderr)
        return False
    
    try:
        result = subprocess.run(['schtasks', '/Query', '/FO', 'LIST'], 
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f'task: Failed to list tasks: {result.stderr}', file=sys.stderr)
            return False
    except Exception as e:
        print(f'task: Error listing tasks: {e}', file=sys.stderr)
        return False


def _remove_task(name: str) -> bool:
    """Remove a scheduled task."""
    if os.name != 'nt':
        print('task: Windows-only feature', file=sys.stderr)
        return False
    
    try:
        result = subprocess.run(['schtasks', '/Delete', '/TN', name, '/F'],
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f'task: Removed task "{name}"')
            return True
        else:
            print(f'task: Failed to remove task: {result.stderr}', file=sys.stderr)
            return False
    except Exception as e:
        print(f'task: Error removing task: {e}', file=sys.stderr)
        return False


def _run_task(name: str) -> bool:
    """Run a scheduled task immediately."""
    if os.name != 'nt':
        print('task: Windows-only feature', file=sys.stderr)
        return False
    
    try:
        result = subprocess.run(['schtasks', '/Run', '/TN', name],
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f'task: Running task "{name}"')
            return True
        else:
            print(f'task: Failed to run task: {result.stderr}', file=sys.stderr)
            return False
    except Exception as e:
        print(f'task: Error running task: {e}', file=sys.stderr)
        return False


def execute(args: List[str]) -> int:
    """Execute the task command."""
    parser = argparse.ArgumentParser(prog='task', add_help=False)
    subparsers = parser.add_subparsers(dest='mode', help='Task mode')
    
    schedule_parser = subparsers.add_parser('schedule', help='Schedule tasks')
    schedule_subparsers = schedule_parser.add_subparsers(dest='action', help='Schedule action')
    
    add_parser = schedule_subparsers.add_parser('add', help='Add scheduled task')
    add_parser.add_argument('name', help='Task name')
    add_parser.add_argument('command', help='Command to run')
    add_parser.add_argument('schedule', help='Schedule (e.g., "daily 2am", "weekly sunday 3am")')
    
    schedule_subparsers.add_parser('list', help='List scheduled tasks')
    
    remove_parser = schedule_subparsers.add_parser('remove', help='Remove scheduled task')
    remove_parser.add_argument('name', help='Task name')
    
    run_parser = schedule_subparsers.add_parser('run', help='Run task immediately')
    run_parser.add_argument('name', help='Task name')
    
    parser.add_argument('-h', '--help', action='store_true', dest='show_help')
    
    ns = parser.parse_args(args)
    if ns.show_help or not ns.mode:
        parser.print_help()
        print()
        print('Examples:')
        print('  task schedule add cleanup "rm -rf ~/tmp/*" "daily 2am"')
        print('  task schedule add backup "cp -r ~/docs ~/backup" "weekly sunday 3am"')
        print('  task schedule list')
        print('  task schedule remove cleanup')
        print('  task schedule run backup')
        print()
        print('Schedule formats:')
        print('  "daily 2am" - Run daily at 2am')
        print('  "weekly sunday 3am" - Run weekly on Sunday at 3am')
        print('  "monthly 1st 1am" - Run monthly on 1st at 1am')
        print('  "14:30" - Run daily at 2:30pm')
        return 0

    if ns.mode == 'schedule':
        if ns.action == 'add':
            if not hasattr(ns, 'name') or not hasattr(ns, 'command') or not hasattr(ns, 'schedule'):
                print('task: name, command, and schedule required', file=sys.stderr)
                return 1
            if _schedule_task(ns.name, ns.command, ns.schedule):
                return 0
            else:
                return 1
        elif ns.action == 'list':
            if _list_tasks():
                return 0
            else:
                return 1
        elif ns.action == 'remove':
            if not hasattr(ns, 'name'):
                print('task: name required', file=sys.stderr)
                return 1
            if _remove_task(ns.name):
                return 0
            else:
                return 1
        elif ns.action == 'run':
            if not hasattr(ns, 'name'):
                print('task: name required', file=sys.stderr)
                return 1
            if _run_task(ns.name):
                return 0
            else:
                return 1

    return 1

