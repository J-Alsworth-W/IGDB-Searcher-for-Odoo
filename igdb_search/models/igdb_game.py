from odoo import api, exceptions, fields, models, modules, _
import requests
import base64
import logging

_logger = logging.getLogger(__name__)


class IgdbGame(models.Model):
    _name = 'igdb.game'
    _description = 'IGDB Game'
    _order = "name ASC, igdb_id ASC"

    name = fields.Char(required=True)
    igdb_id = fields.Integer(string="IGDB ID")
    game_cover = fields.Image(attachment=False)
    game_cover_retrieved = fields.Boolean(default=False)
    first_release_date = fields.Date(string="Initial Release Date")
    platform_ids = fields.Many2many(string="Platforms", comodel_name='igdb.platform', relation="igdb_game_platforms_rel")
    genre_ids = fields.Many2many(string="Genres", comodel_name='igdb.genre', relation="igdb_game_genres_rel")
    theme_ids = fields.Many2many(string="Themes", comodel_name='igdb.theme', relation="igdb_game_themes_rel")
    url = fields.Char(string="IGDB URL")
    query_ids = fields.Many2many(string="Linked Queries", comodel_name='igdb.query', relation="igdb_query_res_games_rel")
    involved_game_company_ids = fields.One2many(string="Involved Game Companies", comodel_name='igdb.involved.game.company',
                                                 inverse_name="game_id")
    developer_ids = fields.Many2many(string="Developer(s)", comodel_name='igdb.game.company',
                                     compute='_compute_developer_publisher_ids', compute_sudo=True)
    publisher_ids = fields.Many2many(string="Publisher(s)", comodel_name='igdb.game.company',
                                     compute='_compute_developer_publisher_ids', compute_sudo=True)
    porter_ids = fields.Many2many(string="Porter(s)", comodel_name='igdb.game.company',
                                  compute='_compute_developer_publisher_ids', compute_sudo=True)
    franchise_ids = fields.Many2many(string="Franchise(s)", comodel_name='igdb.franchise', relation="igdb_games_franchises_rel")

    _check_game_igdb_id_unique = models.Constraint(
        'unique (igdb_id)',
        'The IGDB ID of a game must be unique, this one is already assigned to another game.'
    )

    @api.depends('involved_game_company_ids')
    def _compute_developer_publisher_ids(self):
        for game in self:
            game.developer_ids = self.env['igdb.game.company']
            game.publisher_ids = self.env['igdb.game.company']
            game.porter_ids = self.env['igdb.game.company']

            for igc in game.involved_game_company_ids:
                if igc.is_developer:
                    game.developer_ids += igc.game_company_id
                if igc.is_publisher:
                    game.publisher_ids += igc.game_company_id
                if igc.is_porter:
                    game.porter_ids += igc.game_company_id

    def get_cover(self):
        config = self.env['igdb.config'].get_config()
        config.test_connection()

        covers_list = ", ".join([str(game.igdb_id) for game in self if game.game_cover is not None])

        covers_url = 'https://api.igdb.com/v4/covers'
        covers_query = "fields *; where game = (%s); limit 500;" % covers_list
        covers_response = requests.post(covers_url, headers={'Client-ID': config.client_id_string,
                                           'Authorization': 'Bearer ' + config.access_token},
                                        data=covers_query)
        covers_response.raise_for_status()
        covers_response_json = covers_response.json()

        game_dict = {game: False for game in self}

        for cover in covers_response_json:
            game = self.env['igdb.game'].search([('igdb_id', '=', cover.get('game'))])
            cover_url = "https://images.igdb.com/igdb/image/upload/t_cover_big/%s.jpeg" % cover.get('image_id')
            cover_image_response = requests.get(cover_url)
            cover_image_response.raise_for_status()

            cover_image_response_content = cover_image_response.content
            encoded_cover_image_response_content = base64.b64encode(cover_image_response_content)
            game.game_cover = encoded_cover_image_response_content
            game.game_cover_retrieved = True  # Set true even if there is no image content
            game_dict[game] = True

        # Make double-sure we don't repeatedly call cron on games who have no cover.
        for game in [game_li for game_li in game_dict if game_dict[game_li] is False]:
            game.game_cover_retrieved = True

    def _cron_get_game_covers(self):
        games = self.search([('game_cover', '=', False), ('game_cover_retrieved', '=', False)])
        game_ids = [game.id for game in games]
        games_batches = [games[i:i + 500] for i in range(0, len(games), 500)]

        for batch in games_batches:
            batch.get_cover()
            _logger.info("Game cover %s/%s fetched." % (str(game_ids.index(batch[-1].id) + 1), str(len(game_ids))))
