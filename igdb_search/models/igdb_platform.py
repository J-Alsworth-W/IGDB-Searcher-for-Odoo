from odoo import api, exceptions, fields, models, modules, _
import requests


class IgdbPlatform(models.Model):
    _name = 'igdb.platform'
    _description = 'IGDB Platform'
    _order = "name ASC, igdb_id ASC"

    name = fields.Char(required=True)
    igdb_id = fields.Integer(string="IGDB ID")
    url = fields.Char(string="IGDB URL")

    _check_platform_igdb_id_unique = models.Constraint(
        'unique (igdb_id)',
        'The IGDB ID of a platform must be unique, this one is already assigned to another platform.'
    )

    def populate_platforms(self):
        config = self.env['igdb.config'].get_config()
        config.test_connection()

        platforms_url = 'https://api.igdb.com/v4/platforms'
        platforms_query = "fields *; limit 500;"
        response = requests.post(platforms_url, headers={'Client-ID': config.client_id_string,
                                                     'Authorization': 'Bearer ' + config.access_token},
                                 data=platforms_query)
        response.raise_for_status()
        response_json = response.json()

        if response.status_code == 200:
            for platform in response_json:
                matching_platform = self.env['igdb.platform'].search([('igdb_id', '=', platform.get('id'))]) if platform.get('id') else False
                if not matching_platform and platform.get('id'):
                    self.env['igdb.platform'].create(
                        {
                            'name': platform.get('name'),
                            'igdb_id': platform.get('id'),
                            'url': platform.get('url'),
                        })
                elif matching_platform and platform.get('id'):
                    matching_platform.write(
                        {
                            'name': platform.get('name'),
                            'url': platform.get('url'),
                        }
                    )
