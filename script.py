import argparse
import datetime

from helper import validate_args, get_ip_address_list, make_backup, make_connection, parse_show_version, \
    get_cdp_service_info, time_config, make_report, get_ntp_service_info, close_connection


def main():
    parser = argparse.ArgumentParser(description='DevNet Tool')
    parser.add_argument('--user', type=str, required=True, help='Username')
    parser.add_argument('--password', type=str, required=True, help='Password')
    parser.add_argument('--network', type=str, required=True, help='Management Network')
    parser.add_argument('--ntp-server', type=str, required=True, help='NTP server')

    args = parser.parse_args()

    validate_args(args)

    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")

    output_report = "----SUMMARY----\n"

    for address in get_ip_address_list(args.network):
        print(f'connection started to {address}')

        connection = make_connection(address=address, user=args.user, password=args.password)
        if not connection:
            continue
        print('connection success')

        connection.enable()

        device_info = parse_show_version(connection=connection)
        if bool(device_info) is False:
            print('show version parse failed')
            continue

        make_backup(connection=connection, hostname=device_info['Hostname'], timestamp=timestamp)

        device_cdp_info = get_cdp_service_info(connection=connection, hostname=device_info['Hostname'])

        time_config(
            connection=connection, hostname=device_info['Hostname'], ntp_server=args.ntp_server, timestamp=timestamp)

        ntp_service_info = get_ntp_service_info(connection=connection, hostname=device_info['Hostname'])
        close_connection(connection=connection)

        output_report += make_report(device_info=device_info, cdp_info=device_cdp_info, ntp_info=ntp_service_info)

    print(output_report)


if __name__ == "__main__":
    main()
