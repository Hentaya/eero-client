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
                                     'reboot','dump'],
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
            if args.command == "dump":
                network_details = eero.networks(network['url'])
                devices = eero.devices(network['url'])
                eeros = eero.eeros(network['url'])

                network_id = eero.id_from_url(network['url'])

                with open('network_{}_info.json'.format(network_id), 'w') as output_file:
                    json.dump(network, output_file, indent=2)

                with open('network_{}_details.json'.format(network_id), 'w') as output_file:
                    json.dump(network_details, output_file, indent=2)

                with open('network_{}_devices.json'.format(network_id), 'w') as output_file:
                    json.dump(devices, output_file, indent=2)

                with open('network_{}_eeros.json'.format(network_id), 'w') as output_file:
                    json.dump(eeros, output_file, indent=2)

                print('Wrote dump files for network {}'.format(network_id))
