import ipaddress
import sys
import re
import os

from netmiko import ConnectHandler
from typing import List, Dict

CONFIG_DIR = 'config'


def is_ipv4address(arg: str) -> bool:
    try:
        ipaddress.IPv4Address(arg)
        return True
    except Exception:
        print('Invalid ipv4 address', arg)
        return False


def is_ipv4network(arg: str) -> bool:
    try:
        ipaddress.IPv4Network(arg)
        return True
    except Exception:
        print('Invalid ipv4 network', arg)
        return False


def get_ip_address_list(arg: str) -> List[str]:
    address_list = list(ipaddress.IPv4Network(arg).hosts())
    return map(str, address_list)


def validate_args(param):
    if not is_ipv4network(param.network):
        print(f'bad network {param.network}')
        sys.exit('1')
    if not is_ipv4address(param.ntp_server):
        print(f'bad network {param.ntp_server}')
        sys.exit('1')

    print('Validation passed')


def make_connection(address: str, user: str, password: str):
    connection_params = {
        'device_type': 'cisco_ios',
        'ip': address,
        'username': user,
        'password': password
    }
#     connection_params = {
#         'device_type': 'cisco_ios',
#         'ip': '64.103.37.51',
#         'username': 'developer',
#         'password': 'C1sco12345',
#         'port': 8181
#     }
    try:
        return ConnectHandler(**connection_params)
    except:
        print(f'Connection failed to host {address}')
        return


def close_connection(connection):
    connection.disconnect()

    print('Connection terminated')


def parse_show_version(connection) -> Dict:
    try:
        result = {}
        output = connection.send_command('show version')

        regex_dict = {
            'Software': r"^Cisco\s+IOS.+Software\s+\((?P<Software>\S+)\),\s+Version\s+\S+,\s+RELEASE\s+SOFTWARE\s+\(fc2\)$",
            'Hostname': r"^(?P<Hostname>\S+)\s+uptime\s+is.+$",
            'ModelNumber': r"^Cisco\s+(?P<ModelNumber>\S+).+\(revision.+$"
        }

        for key, pattern in regex_dict.items():
            matches = re.search(pattern, output, re.MULTILINE + re.IGNORECASE)

            if matches:
                result[key] = matches.group(key)
            else:
                continue
        return result

    except Exception:
        return


def make_backup(connection, hostname: str, timestamp: str):
    #create dir if not exists
    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)

    backup_file_name = os.path.join(CONFIG_DIR, f'{hostname}-{timestamp}.txt')

    try:
        output = connection.send_command('show running-config')
        with open(backup_file_name, "w") as file:
            file.write(output)
        print(f'Backup complete for {hostname}')
    except Exception:
        print(f'Backup failed for {hostname}')


def get_cdp_service_info(connection, hostname: str):
    result = {
        'Status': 'Unknown',
        'Peers': 0
    }

    try:
        output = connection.send_command('show cdp neighbors detail')
        if 'is not enabled' in output:
            result['Status'] = 'Off'
        else:
            result['Status'] = 'On'

        result['Peers'] = output.count('Device ID:')
        print(f'Success in cdp info analyzing on {hostname}')

    except Exception:
        print(f'Failed to get cdp service info on {hostname}')

    return result


def get_ntp_service_info(connection, hostname: str):
    result = 'Unknown'

    try:
        output = connection.send_command('show ntp status')
        if 'Clock is synchronized' in output:
            result = 'Sync'
        else:
            result = 'Not in Sync'

        print(f'Success in ntp info analyzing on {hostname}')

    except Exception:
        print(f'Failed to get ntp service info on {hostname}')

    return result


def time_config(connection, hostname: str, ntp_server: str, timestamp: str):

    backup_file_name = os.path.join(CONFIG_DIR, f'{hostname}-{timestamp}.txt')

    config_lines = {
        'ntp': f'ntp server {ntp_server}',
        'timezone': 'clock timezone GMT 0 0'
    }

    try:
        backup_file = open(backup_file_name, "r")
    except:
        print(f'Fail to open backup file for {hostname}. Can\'t continue')

    config = backup_file.read()

    keys_to_config = []

    for key, line in config_lines.items():
        if line not in config:
            print(f'{line} not in config')
            keys_to_config.append(key)

    if 'ntp' in keys_to_config:
        try:
            output = connection.send_command(f'ping {ntp_server}')
            matches = re.search(r"^Success\s+rate\s+is\s+(?P<Rate>\d+)\s+percent.+$", output, re.MULTILINE)
            if matches:
                if int(matches.group('Rate')) > 0:
                    print('ntp server reachable')
                else:
                    print('ntp server not reachable')
                    keys_to_config.remove('ntp')
        except Exception:
            print(f'Failed to check reachibility of ntp server on {hostname}')

    print('config options')
    if len(keys_to_config):
        command_list = [config_lines[item] for item in keys_to_config]
        print(command_list)
        #connection.send_config_set(command_list)
    else:
        print('nothing to config')


def make_report(device_info, cdp_info, ntp_info):
    crypto = 'NPE' if 'npe' in device_info['Software'].lower() else 'PE'
    return f'{device_info["Hostname"]}|{device_info["ModelNumber"]}|{crypto}|CDP is {cdp_info["Status"]}, {cdp_info["Peers"]} Peers|Clock in {ntp_info}\n'
