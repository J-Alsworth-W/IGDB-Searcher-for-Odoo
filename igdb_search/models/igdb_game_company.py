from odoo import api, exceptions, fields, models, modules, _
from odoo.addons.igdb_search.const import COUNTRY_NUMERIC_CODES
import requests


class IgdbCompany(models.Model):
    _name = 'igdb.game.company'
    _description = 'IGDB Company'
    _order = "name ASC, igdb_id ASC"

    name = fields.Char(required=True)
    slug = fields.Char(string="Slug")
    igdb_id = fields.Integer(string="IGDB ID")
    url = fields.Char(string="IGDB URL")
    changed_game_company_id = fields.Many2one(string="New Company ID", comodel_name="igdb.game.company",
                                         help="The new ID for a company that has gone through a merger or "
                                              "restructuring.") # inverse_name on other side
    parent_company_id = fields.Many2one(string="Parent Company", comodel_name="igdb.game.company") # inverse_name on other side
    country_id = fields.Many2one(string="Country", comodel_name="res.country")
    developed_game_ids = fields.Many2many(string="Developed Games", comodel_name="igdb.game",
                                          compute='_compute_game_ids', compute_sudo=True)
    published_game_ids = fields.Many2many(string="Published Games", comodel_name="igdb.game",
                                          compute='_compute_game_ids', compute_sudo=True)
    ported_game_ids = fields.Many2many(string="Ported Games", comodel_name="igdb.game",
                                       compute='_compute_game_ids', compute_sudo=True)
    involved_game_company_ids = fields.One2many(string="Involved Company Records",
                                                comodel_name="igdb.involved.game.company",
                                                inverse_name="game_company_id")

    _check_game_company_igdb_id_unique = models.Constraint(
        'unique (igdb_id)',
        'The IGDB ID of a game company must be unique, this one is already assigned to another game company.'
    )

    @api.depends('involved_game_company_ids')
    def _compute_game_ids(self):
        for company in self:
            company.developed_game_ids = self.env['igdb.game']
            company.published_game_ids = self.env['igdb.game']
            company.ported_game_ids = self.env['igdb.game']

            for igc in company.involved_game_company_ids:
                if igc.is_developer:
                    company.developed_game_ids += igc.game_id
                if igc.is_publisher:
                    company.published_game_ids += igc.game_id
                if igc.is_porter:
                    company.ported_game_ids += igc.game_id

    def populate_game_companies(self):
        config = self.env['igdb.config'].get_config()
        config.test_connection()

        companies_url = 'https://api.igdb.com/v4/companies'
        query_finished = False
        most_recent_company_igdb_id = 0
        new_and_matched_companies = self.env['igdb.game.company']

        while not query_finished:
            # This igdb_id should increase until the entire database for IGDB has been searched and stored.
            companies_query = "fields *; where id > %s; sort id asc; limit 500;" % most_recent_company_igdb_id

            response = requests.post(companies_url, headers={'Client-ID': config.client_id_string,
                                                             'Authorization': 'Bearer ' + config.access_token},
                                     data=companies_query)
            response.raise_for_status()
            response_json = response.json()

            if len(response_json) == 0:
                query_finished = True
                continue

            for company in response_json:
                matching_company = self.env['igdb.game.company'].search([('igdb_id', '=', company.get('id'))]) if company.get('id') else False
                country_code = COUNTRY_NUMERIC_CODES.get(str(company.get('country')), '')
                if not matching_company and company.get('id'):
                    new_company = self.env['igdb.game.company'].create(
                        {
                            'name': company.get('name'),
                            'slug': company.get('slug'),
                            'igdb_id': company.get('id'),
                            'url': company.get('url'),
                            'country_id': self.env['res.country'].search([('code', '=', country_code)]).id,
                        })
                    new_and_matched_companies += new_company
                elif matching_company and company.get('id'):
                    matching_company.write(
                        {
                            'name': company.get('name'),
                            'slug': company.get('slug'),
                            'url': company.get('url'),
                            'country_id': self.env['res.country'].search([('code', '=', country_code)]).id,
                        }
                    )
                    new_and_matched_companies += matching_company

            most_recent_company_igdb_id = new_and_matched_companies[-1].igdb_id
            print("%s company records searched and created/updated." % str(len(new_and_matched_companies)))
