#!/usr/bin/env python
from argparse import ArgumentParser
import json
import eero
import six


class CookieStore(eero.SessionStorage):
    def __init__(self, cookie_file):
        from os import path
        self.cookie_file = path.abspath(cookie_file)

        try:
            with open(self.cookie_file, 'r') as f:
                self.__cookie = f.read()
        except IOError:
            self.__cookie = None

    @property
    def cookie(self):
        return self.__cookie

    @cookie.setter
    def cookie(self, cookie):
        self.__cookie = cookie
        with open(self.cookie_file, 'w+') as f:
            f.write(self.__cookie)


session = CookieStore('session.cookie')
eero = eero.Eero(session)


def print_json(data):
    print(json.dumps(data, indent=4))


if __name__ == '__main__':
    if eero.needs_login():
        parser = ArgumentParser()
        parser.add_argument("-l", help="your eero login (email address or phone number)")
        args = parser.parse_args()
        if args.l:
            phone_number = args.l
        else:
            phone_number = six.moves.input('your eero login (email address or phone number): ')
        user_token = eero.login(phone_number)
        verification_code = six.moves.input('verification key from email or SMS: ')
        eero.login_verify(verification_code, user_token)
        print('Login successful. Rerun this command to get some output')
    else:
        account = eero.account()

        parser = ArgumentParser()
        parser.add_argument("command",
                            choices=['devices', 'details', 'info', 'eeros',
                                     'reboot','dump','topology'],
                            help="info to print")
        parser.add_argument("--eero", type=int, help="eero to reboot")
        args = parser.parse_args()

        for network in account['networks']['data']:
            if args.command == 'info':
                print_json(network)
            if args.command == 'details':
                network_details = eero.networks(network['url'])
                print_json(network_details)
            if args.command == 'devices':
                devices = eero.devices(network['url'])
                print_json(devices)
            if args.command == 'eeros':
                eeros = eero.eeros(network['url'])
                print_json(eeros)
            if args.command == 'reboot':
                reboot = eero.reboot(args.eero)
                print_json(reboot)
            if args.command == 'dump':
                import datetime

                network_details = eero.networks(network['url'])
                devices = eero.devices(network['url'])
                eeros = eero.eeros(network['url'])

                network_dump = {
                    'info': network,
                    'details': network_details,
                    'devices': devices,
                    'eeros': eeros
                }

                network_id = eero.id_from_url(network['url'])
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

                filename = 'network_{}_dump_{}.json'.format(network_id, timestamp)

                with open(filename, 'w') as output_file:
                    json.dump(network_dump, output_file, indent=2)

                print('Wrote dump file {}'.format(filename))          
            if args.command == 'topology':
                devices = eero.devices(network['url'])

                nodes = {}

                for device in devices:
                    source = device.get('source', {})
                    node = source.get('display_name', 'Unknown node')

                    if node not in nodes:
                        nodes[node] = []

                    name = device.get('nickname') or device.get('hostname') or 'Unknown device'

                    connected = device.get('connected', False)
                    if connected:
                        status = 'connected'
                    else:
                        status = 'offline'

                    connection_type = device.get('connection_type', 'unknown')

                    if connection_type == 'wired':
                        overlay = '[{}] (wired)'.format(status)
                    else:
                        connectivity = device.get('connectivity', {})
                        interface = device.get('interface', {})

                        signal = connectivity.get('signal')
                        score_bars = connectivity.get('score_bars')
                        rx_bitrate = connectivity.get('rx_bitrate')
                        frequency = interface.get('frequency')
                        frequency_unit = interface.get('frequency_unit')

                        wifi_details = []

                        if frequency is not None and frequency_unit:
                            wifi_details.append('{} {}'.format(frequency, frequency_unit))

                        if signal is not None:
                            wifi_details.append('signal {}'.format(signal))

                        if score_bars is not None:
                            wifi_details.append('{} bars'.format(score_bars))

                        if rx_bitrate is not None:
                            wifi_details.append('rx {}'.format(rx_bitrate))

                        if wifi_details:
                            overlay = '[{}] (WiFi, {})'.format(status, ', '.join(wifi_details))
                        else:
                            overlay = '[{}] (WiFi)'.format(status)

                    nodes[node].append((name, overlay))

                for node in sorted(nodes.keys()):
                    print(node)

                    devices_for_node = sorted(nodes[node], key=lambda x: x[0].lower())

                    for i, (name, overlay) in enumerate(devices_for_node):
                        branch = '+-'
                        if i == len(devices_for_node) - 1:
                            branch = '`-'

                        print('  {} {} {}'.format(branch, name, overlay))

                    print()
