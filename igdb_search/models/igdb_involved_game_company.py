from odoo import api, exceptions, fields, models, modules, _
import requests


class IgdbInvolvedCompany(models.Model):
    _name = 'igdb.involved.game.company'
    _description = 'IGDB Involved Company'
    _order = "name ASC, igdb_id ASC"

    name = fields.Char(required=False)
    igdb_id = fields.Integer(string="IGDB ID")
    is_developer = fields.Boolean(string="Is Developer")
    is_publisher = fields.Boolean(string="Is Publisher")
    is_porter = fields.Boolean(string="Is Porter")
    game_company_id = fields.Many2one(string="Base Company", comodel_name="igdb.game.company")  # inverse_name on other side
    game_id = fields.Many2one(string="Game", comodel_name="igdb.game")

    _check_involved_game_company_igdb_id_unique = models.Constraint(
        'unique (igdb_id)',
        'The IGDB ID of an involved game company must be unique, this one is already assigned to another involved game '
        'company.'
    )