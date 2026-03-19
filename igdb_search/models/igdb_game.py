from odoo import api, exceptions, fields, models, modules, _


class IgdbGame(models.Model):
    _name = 'igdb.game'
    _description = 'IGDB Game'
    _order = "name ASC, igdb_id ASC"

    name = fields.Char(required=True)
    igdb_id = fields.Integer(string="IGDB ID")
    game_cover = fields.Image(attachment=False)
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
