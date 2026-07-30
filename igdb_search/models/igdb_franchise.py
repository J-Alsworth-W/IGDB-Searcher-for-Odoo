from odoo import api, exceptions, fields, models, modules, _
import requests
import logging

_logger = logging.getLogger(__name__)


class IgdbFranchise(models.Model):
    _name = 'igdb.franchise'
    _description = 'IGDB Franchise'
    _order = "name ASC, igdb_id ASC"

    name = fields.Char(required=True)
    igdb_id = fields.Integer(string="IGDB ID")
    game_ids = fields.Many2many(string="Games", comodel_name="igdb.game", relation="igdb_games_franchises_rel")
    slug = fields.Char(string="Slug")
    url = fields.Char(string="IGDB URL")

    _check_franchise_igdb_id_unique = models.Constraint(
        'unique (igdb_id)',
        'The IGDB ID of a franchise must be unique, this one is already assigned to another franchise.'
    )

    def populate_franchises(self):
        config = self.env['igdb.config'].get_config()
        config.test_connection()

        franchises_url = 'https://api.igdb.com/v4/franchises'
        query_finished = False
        most_recent_franchise_igdb_id = 0
        new_and_matched_franchises = self.env['igdb.franchise']

        while not query_finished:
            franchises_query = "fields *; where id > %s; sort id asc; limit 500;" % most_recent_franchise_igdb_id


            response = requests.post(franchises_url, headers={'Client-ID': config.client_id_string,
                                                          'Authorization': 'Bearer ' + config.access_token},
                                     data=franchises_query)
            response.raise_for_status()
            response_json = response.json()

            if len(response_json) == 0:
                query_finished = True
                continue

            if response.status_code == 200:
                for franchise in response_json:
                    matching_franchise = self.env['igdb.franchise'].search([('igdb_id', '=', franchise.get('id'))]) if franchise.get('id') else False
                    if not matching_franchise and franchise.get('id'):
                        new_franchise = self.env['igdb.franchise'].create(
                            {
                                'name': franchise.get('name'),
                                'slug': franchise.get('slug'),
                                'igdb_id': franchise.get('id'),
                                'url': franchise.get('url'),
                            })
                        new_and_matched_franchises += new_franchise
                    elif matching_franchise and franchise.get('id'):
                        matching_franchise.write(
                            {
                                'name': franchise.get('name'),
                                'slug': franchise.get('slug'),
                                'url': franchise.get('url'),
                            }
                        )
                        new_and_matched_franchises += matching_franchise

                most_recent_franchise_igdb_id = new_and_matched_franchises[-1].igdb_id
                _logger.info("%s franchise records searched and created/updated." % str(len(new_and_matched_franchises)))