import argparse

from utils import validate_args, get_ip_address_list, make_connection, close_connection
from tasks import make_backup, config_timezone_ntp, make_report
from parsers import parse_show_version, parse_cdp_neighbor_detail, parse_ntp_status


def main():
    parser = argparse.ArgumentParser(description='DevNet Tool')
    parser.add_argument('--user', type=str, required=True, help='Username')
    parser.add_argument('--password', type=str, required=True, help='Password')
    parser.add_argument('--network', type=str, required=True, help='Management Network')
    parser.add_argument('--ntp-server', type=str, required=True, help='NTP server')

    args = parser.parse_args()

    validate_args(args)

    output_report = ''

    for address in get_ip_address_list(args.network):
        print(f'connection started to {address}')

        connection = make_connection(address=address, user=args.user, password=args.password)
        if not connection:
            continue
        print('connection success')

        connection.enable()

        device_info = parse_show_version(connection=connection)
        if bool(device_info) is False:
            print('show version parse failed, skip')
            continue

        config = make_backup(connection=connection, hostname=device_info['Hostname'])
        if not config:
            print('failed to get config, skip')
            continue

        device_cdp_info = parse_cdp_neighbor_detail(connection=connection, hostname=device_info['Hostname'])

        config_timezone_ntp(
            connection=connection, hostname=device_info['Hostname'], ntp_server=args.ntp_server, config=config)

        ntp_service_info = parse_ntp_status(connection=connection, hostname=device_info['Hostname'])

        close_connection(connection=connection)

        output_report += make_report(device_info=device_info, cdp_info=device_cdp_info, ntp_info=ntp_service_info)

    if output_report:
        print('----SUMMARY----\n')
        print(output_report)


if __name__ == "__main__":
    main()
