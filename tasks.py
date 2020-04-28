import os
import re
import datetime

from utils import execute_command, is_one

CONFIG_DIR = 'config'


def make_backup(connection, hostname: str, timestamp: str) -> str:
    data = execute_command(connection, 'show running-config')
    if not is_one(data):
        return

    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)

    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")
    backup_file_name = os.path.join(CONFIG_DIR, f'{hostname}-{timestamp}.txt')

    try:
        file = open(backup_file_name, "w")
    except OSError:
        print(f'Backup failed for {hostname}')
    else:
        file.write(data['Data'])
        file.close()
        print(f'Backup complete for {hostname}')

    return data['Data']


def config_timezone_ntp(connection, hostname: str, ntp_server: str, config: str):
    config_lines = {
        'ntp': f'ntp server {ntp_server}',
        'timezone': 'clock timezone GMT 0 0'
    }

    keys_to_config = []

    for key, line in config_lines.items():
        if line not in config:
            print(f'{line} not in config')
            keys_to_config.append(key)

    if 'ntp' in keys_to_config:
        data = execute_command(connection, f'ping {ntp_server}')
        if not is_one(data):
            return

        match = re.search(r"^Success\s+rate\s+is\s+(?P<Rate>\d+)\s+percent.+$", data['Data'], re.MULTILINE)
        if match and int(match.group('Rate')) == 0:
            print(f'ntp server not reachable from {hostname}')
            keys_to_config.remove('ntp')

    if len(keys_to_config):
        command_list = [config_lines[item] for item in keys_to_config]
        print(f'need to execute commands: {command_list}')
        #just for test
        #connection.send_config_set(command_list)
    else:
        print(f'nothing to change in config on {hostname}')


def make_report(device_info, cdp_info, ntp_info):
    crypto = 'NPE' if 'npe' in device_info['Software'].lower() else 'PE'
    return f"{device_info['Hostname']}|{device_info['ModelNumber']}|" \
        f"{crypto}|CDP is {cdp_info['Status']}, {cdp_info['Peers']} Peers|" \
        f"Clock in {ntp_info['Status']}\n"

