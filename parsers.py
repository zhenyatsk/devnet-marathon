import re
from utils import is_one, execute_command
from typing import Dict


def multiple_pattern_regex(patterns: Dict, data: str, flags: int) -> Dict:
    result = {}

    for key, pattern in patterns.items():
        match = re.search(pattern, data, flags)
        if match:
            result[key] = match.group(key)
        else:
            continue

    return result


def parse_show_version(connection) -> Dict:
    data = execute_command(connection, 'show version')
    if not is_one(data):
        return {}

    regex_dict = {
        'Software': r"^Cisco\s+IOS.+Software\s+\((?P<Software>\S+)\),\s+Version\s+\S+,\s+RELEASE\s+SOFTWARE\s+\(fc2\)$",
        'Hostname': r"^(?P<Hostname>\S+)\s+uptime\s+is.+$",
        'ModelNumber': r"^Cisco\s+(?P<ModelNumber>\S+).+\(revision.+$"
    }

    return multiple_pattern_regex(regex_dict, data['Data'], re.MULTILINE + re.IGNORECASE)


def parse_cdp_neighbor_detail(connection, hostname: str) -> Dict:
    result = {
        'Status': 'Off',
        'Peers': 0
    }

    data = execute_command(connection, 'show cdp neighbors detail')
    if not is_one(data):
        print(f'Failed to get cdp service info on {hostname}')
        return result

    if 'is not enabled' not in data['Data']:
        result['Status'] = True
        result['Peers'] = data['Data'].count('Device ID:')

    print(f'Success in cdp info analyzing on {hostname}')

    return result


def parse_ntp_status(connection, hostname: str) -> Dict:
    data = execute_command(connection, 'show ntp status')
    if not is_one(data):
        print(f'Failed to get ntp service info on {hostname}')
        return {}

    result = {
        'Status': 'Not sync'
    }

    if 'Clock is synchronized' in data['Data']:
        result['Status'] = 'Sync'

    return result
