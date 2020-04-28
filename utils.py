import ipaddress
import sys

from netmiko import ConnectHandler
from typing import List, Dict


def is_one(arg: Dict):
    return True if len(arg) == 1 else False


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
    # connection_params = {
    #     'device_type': 'cisco_ios',
    #     'ip': '64.103.37.51',
    #     'username': 'developer',
    #     'password': 'C1sco12345',
    #     'port': 8181
    # }
    try:
        return ConnectHandler(**connection_params)
    except:
        print(f'Connection failed to host {address}')
        return


def close_connection(connection):
    connection.disconnect()

    print('Connection terminated')


COMMAND_ERROR_PATTERN = ['Invalid input detected at ']


def execute_command(connection, command: str) -> Dict:
    result = {
        'Data': None
    }

    try:
        output = connection.send_command(command)

        command_error = False
        for item in COMMAND_ERROR_PATTERN:
            if item in output:
                command_error = True

        if command_error:
            result['Error'] = 'Command Error'
        else:
            result['Data'] = output

    except Exception as error:
        result['Error'] = error

    return result
