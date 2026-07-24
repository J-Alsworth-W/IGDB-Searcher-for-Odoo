import datetime
from datetime import timedelta

from odoo import api, exceptions, fields, models, modules, _
import requests
import logging

_logger = logging.getLogger(__name__)


class IgdbConfig(models.Model):
    _name = 'igdb.config'
    _description = 'IGDB Config'

    client_id_string = fields.Char("Client ID", required=True, store=True)
    client_secret = fields.Char("Client Secret", required=True, store=True)
    auth_token_url = fields.Char("Twitch Auth URL", required=True, store=True)
    access_token = fields.Char("Access Token")
    expiry_time = fields.Datetime("Access Token Expiry Time")
    active = fields.Boolean(default=True)

    def test_connection(self):
        if self.expiry_time and self.expiry_time - datetime.datetime.now() >= timedelta(days=1):
            return self
        else:
            access_token = requests.post(self.auth_token_url, data={'client_id': self.client_id_string,
                                                                    'client_secret': self.client_secret,
                                                                    'grant_type': "client_credentials"})

            if access_token:
                try:
                    response_json = access_token.json()
                    self.access_token = response_json.get('access_token')
                    expires_in = response_json.get('expires_in')
                    self.expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
                except Exception as e:
                    raise Exception(access_token)
            else:
                raise exceptions.ValidationError("Connection failed!")

            return self

    def get_config(self):
        configs = self.env['igdb.config'].search([])
        return configs[0] if configs else False
