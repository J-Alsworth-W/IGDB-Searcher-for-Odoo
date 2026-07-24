from odoo import api, exceptions, fields, models, modules, _
import requests


class IgdbPerspective(models.Model):
    _name = 'igdb.perspective'
    _description = 'IGDB Perspective'
    _order = "name ASC, igdb_id ASC"

    name = fields.Char(required=True)
    slug = fields.Char(string="Slug")
    igdb_id = fields.Integer(string="IGDB ID")
    url = fields.Char(string="IGDB URL")

    _check_perspective_igdb_id_unique = models.Constraint(
        'unique (igdb_id)',
        'The IGDB ID of a perspective must be unique, this one is already assigned to another perspective.'
    )

    def populate_perspectives(self):
        config = self.env['igdb.config'].get_config()
        config.test_connection()

        perspectives_url = 'https://api.igdb.com/v4/player_perspectives'
        perspectives_query = "fields *; limit 500;"
        response = requests.post(perspectives_url, headers={'Client-ID': config.client_id_string,
                                                      'Authorization': 'Bearer ' + config.access_token},
                                 data=perspectives_query)
        response.raise_for_status()
        response_json = response.json()

        if response.status_code == 200:
            for perspective in response_json:
                matching_perspective = self.env['igdb.perspective'].search([('igdb_id', '=', perspective.get('id'))]) if perspective.get('id') else False
                if not matching_perspective and perspective.get('id'):
                    self.env['igdb.perspective'].create(
                        {
                            'name': perspective.get('name'),
                            'slug': perspective.get('slug'),
                            'igdb_id': perspective.get('id'),
                            'url': perspective.get('url'),
                        })
                elif matching_perspective and perspective.get('id'):
                    matching_perspective.write(
                        {
                            'name': perspective.get('name'),
                            'slug': perspective.get('slug'),
                            'url': perspective.get('url'),
                        }
                    )
