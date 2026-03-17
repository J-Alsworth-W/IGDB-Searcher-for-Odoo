from odoo import api, exceptions, fields, models, modules, _
import requests


class IgdbGenre(models.Model):
    _name = 'igdb.genre'
    _description = 'IGDB Genre'
    _order = "name ASC, igdb_id ASC"

    name = fields.Char(required=True)
    slug = fields.Char(string="Slug")
    igdb_id = fields.Integer(string="IGDB ID")
    url = fields.Char(string="IGDB URL")

    _check_genre_igdb_id_unique = models.Constraint(
        'unique (igdb_id)',
        'The IGDB ID of a genre must be unique, this one is already assigned to another genre.'
    )

    def populate_genres(self):
        config = self.env['igdb.config'].get_config()
        config.test_connection()

        genres_url = 'https://api.igdb.com/v4/genres'
        genres_query = "fields *; limit 500;"
        response = requests.post(genres_url, headers={'Client-ID': config.client_id_string,
                                                      'Authorization': 'Bearer ' + config.access_token},
                                 data=genres_query)
        response.raise_for_status()
        response_json = response.json()

        if response.status_code == 200:
            for genre in response_json:
                matching_genre = self.env['igdb.genre'].search([('igdb_id', '=', genre.get('id'))]) if genre.get('id') else False
                if not matching_genre and genre.get('id'):
                    self.env['igdb.genre'].create(
                        {
                            'name': genre.get('name'),
                            'slug': genre.get('slug'),
                            'igdb_id': genre.get('id'),
                            'url': genre.get('url'),
                        })
                elif matching_genre and genre.get('id'):
                    matching_genre.write(
                        {
                            'name': genre.get('name'),
                            'slug': genre.get('slug'),
                            'url': genre.get('url'),
                        }
                    )
