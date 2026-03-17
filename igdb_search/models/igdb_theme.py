from odoo import api, exceptions, fields, models, modules, _
import requests


class IgdbTheme(models.Model):
    _name = 'igdb.theme'
    _description = 'IGDB Theme'
    _order = "name ASC, igdb_id ASC"

    name = fields.Char(required=True)
    slug = fields.Char(string="Slug")
    igdb_id = fields.Integer(string="IGDB ID")
    url = fields.Char(string="IGDB URL")

    _check_theme_igdb_id_unique = models.Constraint(
        'unique (igdb_id)',
        'The IGDB ID of a theme must be unique, this one is already assigned to another theme.'
    )

    def populate_themes(self):
        config = self.env['igdb.config'].get_config()
        config.test_connection()

        themes_url = 'https://api.igdb.com/v4/themes'
        themes_query = "fields *; limit 500;"
        response = requests.post(themes_url, headers={'Client-ID': config.client_id_string,
                                                      'Authorization': 'Bearer ' + config.access_token},
                                 data=themes_query)
        response.raise_for_status()
        response_json = response.json()

        if response.status_code == 200:
            for theme in response_json:
                matching_theme = self.env['igdb.theme'].search([('igdb_id', '=', theme.get('id'))]) if theme.get('id') else False
                if not matching_theme and theme.get('id'):
                    self.env['igdb.theme'].create(
                        {
                            'name': theme.get('name'),
                            'slug': theme.get('slug'),
                            'igdb_id': theme.get('id'),
                            'url': theme.get('url'),
                        })
                elif matching_theme and theme.get('id'):
                    matching_theme.write(
                        {
                            'name': genre.get('name'),
                            'slug': theme.get('slug'),
                            'url': theme.get('url'),
                        }
                    )
