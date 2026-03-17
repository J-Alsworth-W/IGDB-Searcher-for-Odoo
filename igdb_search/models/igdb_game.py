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

    _check_game_igdb_id_unique = models.Constraint(
        'unique (igdb_id)',
        'The IGDB ID of a game must be unique, this one is already assigned to another game.'
    )