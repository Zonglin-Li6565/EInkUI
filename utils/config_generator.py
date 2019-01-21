import argparse
import configparser
import os
from configparser import ConfigParser

from google.oauth2.credentials import Credentials

from model.events import GoogleCalendarEvents


class Configurations:
    def __init__(self, config: ConfigParser):
        self._owm_token = config.get('API_KEYS', 'OWM', fallback='')
        self._google_token = config.get('API_KEYS', 'Google_Token', fallback='')
        self._google_refresh_token = config.get('API_KEYS',
                                                'Google_Refresh_Token',
                                                fallback='')
        self._google_client_id = config.get('API_KEYS', 'Google_Client_Id',
                                            fallback='')
        self._google_client_secrete = config.get('API_KEYS',
                                                 'Google_Client_Secrete',
                                                 fallback='')

        self._units = config.get('CONFIG', 'Units', fallback='celsius')
        self._city_id = config.getint('CONFIG', 'City_Id', fallback=0)
        self._selected_calendars = []
        selected_calendars = config.get('CONFIG', 'Selected_Calendars',
                                        fallback='')
        for calendar_id in map(lambda s: s.strip(),
                               selected_calendars.split(',')):
            self._selected_calendars.append(calendar_id)

        self._debug_save_path = ''

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, units: str):
        self._units = units

    @property
    def owm_token(self):
        return self._owm_token

    @owm_token.setter
    def owm_token(self, owm_token: str):
        self._owm_token = owm_token

    @property
    def google_credentials(self):
        return Credentials(
            self._google_token,
            refresh_token=self._google_refresh_token,
            client_id=self._google_client_id,
            client_secret=self._google_client_secrete,
            token_uri='https://accounts.google.com/o/oauth2/token')

    @property
    def google_token(self):
        return self._google_token

    @google_token.setter
    def google_token(self, google_token):
        self._google_token = google_token

    @property
    def google_refresh_token(self):
        return self._google_refresh_token

    @google_refresh_token.setter
    def google_refresh_token(self, google_refresh_token):
        self._google_refresh_token = google_refresh_token

    @property
    def google_client_id(self):
        return self._google_client_id

    @google_client_id.setter
    def google_client_id(self, google_client_id):
        self._google_client_id = google_client_id

    @property
    def google_client_secrete(self):
        return self._google_client_secrete

    @google_client_secrete.setter
    def google_client_secrete(self, google_client_secrete):
        self._google_client_secrete = google_client_secrete

    @property
    def selected_calendars(self):
        return self._selected_calendars

    @property
    def city_id(self):
        return self._city_id

    @city_id.setter
    def city_id(self, city_id: int):
        self._city_id = city_id

    @property
    def is_debug(self):
        return len(self._debug_save_path) > 0

    @property
    def debug_save_path(self):
        return self._debug_save_path

    @debug_save_path.setter
    def debug_save_path(self, path):
        self._debug_save_path = path

    def add_selected_calendars(self, calendar_id: str):
        self._selected_calendars.append(calendar_id)

    def save(self, file_path):
        config = configparser.ConfigParser()
        config.add_section('API_KEYS')
        config.set('API_KEYS', 'OWM', self.owm_token)
        config.set('API_KEYS', 'Google_Token', self._google_token)
        config.set('API_KEYS', 'Google_Refresh_Token',
                   self._google_refresh_token)
        config.set('API_KEYS', 'Google_Client_Id', self._google_client_id)
        config.set('API_KEYS', 'Google_Client_Secrete',
                   self._google_client_secrete)

        config.add_section('CONFIG')
        config.set('CONFIG', 'City_Id', str(self.city_id))
        config.set('CONFIG', 'Units', self.units)
        selected_calendars = ','.join(self.selected_calendars)
        config.set('CONFIG', 'Selected_Calendars', selected_calendars)

        with open(file_path, 'w') as file:
            config.write(file)


def load_or_create_config():
    parser = argparse.ArgumentParser('EInk Smart Calendar')
    parser.add_argument('-c', '--config', type=str,
                        help='Path for the config file')
    parser.add_argument('-d', '--debug', type=str,
                        help='Path for generating debug images')
    args = parser.parse_args()
    if args.config is not None and os.path.isfile(args.config):
        config = configparser.ConfigParser()
        with open(args.config, 'r') as file:
            config_str = file.read()
            config.read_string(config_str)
        config_obj = Configurations(config)
    else:
        config_obj = Configurations(configparser.ConfigParser())
        config_obj.owm_token = input('Paste in the Open Weather Map Token: \n')
        print('To generate Google API tokens, see the video'
              + ' https://www.youtube.com/watch?v=hfWe1gPCnzc')
        config_obj.google_token = input('Paste in the Access Token: \n')
        config_obj.google_refresh_token = input(
            'Paste in the Refresh Token: \n')
        config_obj.google_client_id = input('Paste in the Client ID: \n')
        config_obj.google_client_secrete = input(
            'Paste in the Client Secrete: \n')

        print('Retrieving calendars ...')
        credentials = config_obj.google_credentials
        google_calendar = GoogleCalendarEvents(credentials)
        list_calendars = google_calendar.list_calendars()
        for i in range(len(list_calendars)):
            print('%d) %s' % (i, list_calendars[i][1]))
        selected_calendars = []
        prompt = ('Select one or more calendars by listing out'
                  + ' their index. Separated by \',\'\n')
        while True:
            selections = input(prompt)
            selections = map(lambda s: int(s.strip()), selections.split(','))
            for index in selections:
                if index >= len(list_calendars):
                    prompt = 'Invalid index. Try again \n'
                    break
                selected_calendars.append(list_calendars[index][0])
            else:
                break
            selected_calendars = []

        for selected_calendar in selected_calendars:
            config_obj.add_selected_calendars(selected_calendar)

        city_id = int(input('Paste in the city id for retrieving weather.'
                            + ' The city id could be found on Open Weather'
                            + ' Map website: \n'))
        config_obj.city_id = city_id
        prompt = ('Now select the unit for temperature.'
                  + ' Either "fahrenheit" or "celsius" \n')
        while True:
            units = input(prompt)
            if units != 'fahrenheit' and units != 'celsius':
                prompt = 'Invalid selection. Try again'
            else:
                break

        config_obj.units = units

        saving_path = input('Now provide a path for saving the config \n')

        config_obj.save(saving_path)

        abs_path = os.path.abspath(saving_path)
        print(('Congratulations, configuration is done. The file has been saved'
               + ' to %s. Later runs should specify the arguments:'
               + ' -c %s') % (abs_path, abs_path))

    if args.debug is not None:
        config_obj.debug_save_path = args.debug

    return config_obj
