from odoo import api, exceptions, fields, models, modules, _
from odoo.fields import Command
from odoo.addons.igdb_search.const import COUNTRY_NUMERIC_CODES
import requests
import re
from datetime import date, datetime
from collections import defaultdict
import base64
from PIL import Image


class IgdbQuery(models.Model):
    _name = 'igdb.query'
    _description = 'IGDB Query'
    _order = "create_date ASC, id ASC"

    name = fields.Char()
    concatenated_query = fields.Char(compute='_compute_concatenated_query')
    game_name = fields.Char(string="Game Name")
    included_platform_ids = fields.Many2many(string="Platforms", comodel_name='igdb.platform',
                                             relation="igdb_query_inc_platforms_rel")
    excluded_platform_ids = fields.Many2many(string="Excluded Platforms", comodel_name='igdb.platform',
                                             relation="igdb_query_exc_platforms_rel")
    included_genre_ids = fields.Many2many(string="Genres", comodel_name='igdb.genre',
                                             relation="igdb_query_inc_genres_rel")
    excluded_genre_ids = fields.Many2many(string="Excluded Genres", comodel_name='igdb.genre',
                                             relation="igdb_query_exc_genres_rel")
    included_theme_ids = fields.Many2many(string="Themes", comodel_name='igdb.theme',
                                             relation="igdb_query_inc_themes_rel")
    excluded_theme_ids = fields.Many2many(string="Excluded Themes", comodel_name='igdb.theme',
                                             relation="igdb_query_exc_themes_rel")
    included_developer_ids = fields.Many2many(string="Included Developers", comodel_name='igdb.game.company',
                                              relation="igdb_query_inc_devs_rel")
    excluded_developer_ids = fields.Many2many(string="Excluded Developers", comodel_name='igdb.game.company',
                                              relation="igdb_query_exc_devs_rel")
    included_publisher_ids = fields.Many2many(string="Included Publishers", comodel_name='igdb.game.company',
                                              relation="igdb_query_inc_pubs_rel")
    excluded_publisher_ids = fields.Many2many(string="Excluded Publishers", comodel_name='igdb.game.company',
                                              relation="igdb_query_exc_pubs_rel")
    # Todo: add porters or no? Are they useful to know or search?

    result_game_ids = fields.Many2many(string="Returned Games", comodel_name='igdb.game',
                                       relation="igdb_query_res_games_rel", copy=False)
    release_date_start = fields.Date(string="Initial Release Date (Start)")
    release_date_end = fields.Date(string="Initial Release Date (End)")
    search_completed = fields.Boolean(string="Search Completed", default=False, copy=False)
    where_clause_used = fields.Boolean(compute='_compute_concatenated_query')
    num_game_limit = fields.Integer(string="Max. Query Results Limit", default=4000,
                                    help="The upper limit of results that will be returned by the query from IGDB. "
                                         "This cannot exceed 4000 due to technical constraints on the API.")
    # Todo: can raise limit if do_search() reworked to work like populate_game_companies() with searching by sorted ids.
    # Todo: Add player perspective as its own model type here.

    @api.constrains('release_date_start', 'release_date_end')
    def _check_dates(self):
        for query in self:
            if query.release_date_end and query.release_date_start > query.release_date_end:
                raise exceptions.ValidationError("The start date (%s) of the search must be earlier than the end date "
                                                 "(%s)." % (query.release_date_start, query.release_date_end))

    @api.constrains('num_game_limit')
    def _check_num_game_limit(self):
        for query in self:
            if query.num_game_limit > 4000:
                raise exceptions.ValidationError("The Max. Query Results Limit cannot exceed 4000.")

    @api.depends('game_name', 'num_game_limit', 'included_platform_ids', 'excluded_platform_ids', 'included_genre_ids',
                 'excluded_genre_ids', 'included_theme_ids', 'excluded_theme_ids', 'included_developer_ids',
                 'excluded_developer_ids', 'included_publisher_ids', 'excluded_publisher_ids','release_date_start',
                 'release_date_end')
    def _compute_concatenated_query(self):
        for query in self:
            where_clause_used = False

            concat_query = "fields *;"
            if query.game_name:
                concat_query += ' search "%s";' % query.game_name

            if any(query.included_platform_ids or query.excluded_platform_ids or query.included_genre_ids or
                   query.excluded_genre_ids or query.included_theme_ids or query.excluded_theme_ids):
                # or query.included_developer_ids or query.excluded_developer_ids or query.included_publisher_ids or query.excluded_publisher_ids):
                # Todo: check for start and end date here too. Currently missing.
                concat_query += " where"

                if query.included_platform_ids:
                    included_platform_ids = [str(igdb_id) for igdb_id in query.included_platform_ids.mapped('igdb_id')]
                    concat_query += " platforms = [%s]" % (",".join(included_platform_ids))
                    where_clause_used = True
                if query.excluded_platform_ids:
                    if where_clause_used:
                        concat_query += " &"
                    excluded_platform_ids = [str(igdb_id) for igdb_id in query.excluded_platform_ids.mapped('igdb_id')]
                    concat_query += " platforms != (%s)" % (",".join(excluded_platform_ids))
                    where_clause_used = True

                if query.included_genre_ids:
                    if where_clause_used:
                        concat_query += " &"
                    included_genre_ids = [str(igdb_id) for igdb_id in query.included_genre_ids.mapped('igdb_id')]
                    concat_query += " genres = [%s]" % (",".join(included_genre_ids))
                    where_clause_used = True
                if query.excluded_genre_ids:
                    if where_clause_used:
                        concat_query += " &"
                    excluded_genre_ids = [str(igdb_id) for igdb_id in query.excluded_genre_ids.mapped('igdb_id')]
                    concat_query += " genres != (%s)" % (",".join(excluded_genre_ids))
                    where_clause_used = True

                if query.included_theme_ids:
                    if where_clause_used:
                        concat_query += " &"
                    included_theme_ids = [str(igdb_id) for igdb_id in query.included_theme_ids.mapped('igdb_id')]
                    concat_query += " themes = [%s]" % (",".join(included_theme_ids))
                    where_clause_used = True
                if query.excluded_theme_ids:
                    if where_clause_used:
                        concat_query += " &"
                    excluded_theme_ids = [str(igdb_id) for igdb_id in query.excluded_theme_ids.mapped('igdb_id')]
                    concat_query += " themes != (%s)" % (",".join(excluded_theme_ids))
                    where_clause_used = True

                # Todo: implement searching for specific devs + publishers, not currently working.
                # Below is commented out due to searching the API with "involved_companies.company" not being valid.
                # Will have to be done by filtering the results post-retrieval.

                # if query.included_developer_ids or query.included_publisher_ids:
                #     if where_clause_used:
                #         concat_query += " &"
                #     included_company_ids = [str(igdb_id) for igdb_id in query.included_developer_ids.mapped('igdb_id')
                #                             + query.included_publisher_ids.mapped('igdb_id')]
                #     concat_query += " involved_companies.company = [%s]" % (",".join(included_company_ids))
                #     where_clause_used = True
                #
                # if query.excluded_developer_ids or query.excluded_publisher_ids:
                #     if where_clause_used:
                #         concat_query += " &"
                #     excluded_company_ids = [str(igdb_id) for igdb_id in query.excluded_developer_ids.mapped('igdb_id')
                #                             + query.excluded_publisher_ids.mapped('igdb_id')]
                #     concat_query += " involved_companies.company != (%s)" % (",".join(excluded_company_ids))
                #     where_clause_used = True

                if query.release_date_start:
                    if where_clause_used:
                        concat_query += " &"
                    rds_datetime = int((datetime.combine(query.release_date_start, datetime.min.time())).timestamp())
                    concat_query += " first_release_date > %s" % rds_datetime
                    where_clause_used = True
                if query.release_date_end:
                    if where_clause_used:
                        concat_query += " &"
                    rde_datetime = int((datetime.combine(query.release_date_end, datetime.max.time())).timestamp())
                    concat_query += " first_release_date < %s" % rde_datetime
                    where_clause_used = True

            if where_clause_used:
                concat_query += "; limit 500;"
            else:
                concat_query += " limit 500;"

            query.concatenated_query = concat_query if concat_query != "fields *;" else ""
            query.where_clause_used = where_clause_used

    def do_search(self):
        config = self.env['igdb.config'].get_config()
        config.test_connection()

        for query in self:
            games_url = 'https://api.igdb.com/v4/games'
            games_query_finished = False

            retrieved_igdb_ids = []
            retrieved_igdb_ids_str = ""
            igdb_replacement_regex = r"((where id.*)|(& id.*))*(; limit)"
            limit_replacement_regex = r"limit \d*"

            created_games = self.env['igdb.game']
            matching_games = self.env['igdb.game']
            game_igc_dict = {}
            games_to_search = 500

            detailed_query = query.concatenated_query

            while not games_query_finished:
                # Check if next search would take us over the configured query results limit and adjust query accordingly.
                if len(retrieved_igdb_ids) + games_to_search >= query.num_game_limit:
                    games_to_search = query.num_game_limit - len(retrieved_igdb_ids)
                    detailed_query = re.sub(limit_replacement_regex, "limit %s" % games_to_search,
                                            detailed_query)
                elif len(retrieved_igdb_ids) >= query.num_game_limit:
                    games_query_finished = True
                    continue

                # If 2nd+ iteration of while loop
                if retrieved_igdb_ids_str:
                    where_clause_str = " &" if query.where_clause_used else " where"
                    game_reference = "id" if query.game_name else "id"

                    new_ids_search_str = ";" if query.game_name else ""
                    new_ids_search_str += where_clause_str + " %s != (%s); limit" % (game_reference, retrieved_igdb_ids_str)

                    detailed_query = re.sub(igdb_replacement_regex, new_ids_search_str,
                                            detailed_query)
                # If 1st iteration
                else:
                    if query.where_clause_used:
                        detailed_query = re.sub(igdb_replacement_regex, retrieved_igdb_ids_str + "; limit",
                                                detailed_query)
                    else:
                        detailed_query = re.sub(igdb_replacement_regex + ";", retrieved_igdb_ids_str + "; limit",
                                                detailed_query)

                response = requests.post(games_url, headers={'Client-ID': config.client_id_string,
                                                       'Authorization': 'Bearer ' + config.access_token},
                                         data=detailed_query)
                response.raise_for_status()
                response_json = response.json()

                # The 2nd clause here is to address a bug in the API where despite the detailed_query specifically
                # excluding results with matching IDs, they will still be retrieved by the request anyway.
                if (len(response_json) == 0
                        or retrieved_igdb_ids and query.game_name and retrieved_igdb_ids == [str(game.get('id')) for game in response_json]
                        or len(retrieved_igdb_ids) >= query.num_game_limit):  # Todo: unsure if buggy if >500 results in 2nd case, may infinitely loop
                    games_query_finished = True
                    continue

                for game in response_json:
                    matching_game = self.env['igdb.game'].search(
                        [('igdb_id', '=', game.get('id'))]) if game.get('id') else False
                    involved_game_company_ids = game.get('involved_companies')
                    if not matching_game and game.get('id'):
                        new_game = self.env['igdb.game'].create(
                            {
                                'name': game.get('name'),
                                'igdb_id': game.get('id'),
                                'url': game.get('url'),
                                'first_release_date': datetime.fromtimestamp(game.get('first_release_date'), tz=None) if game.get('first_release_date') else False,
                                'platform_ids': self.env['igdb.platform'].search([('igdb_id', '=', game.get('platforms'))]).ids,
                                'genre_ids': self.env['igdb.genre'].search([('igdb_id', '=', game.get('genres'))]).ids,
                                'theme_ids': self.env['igdb.theme'].search([('igdb_id', '=', game.get('themes'))]).ids,
                            })
                        created_games += new_game
                        game_igc_dict[new_game] = involved_game_company_ids
                    elif matching_game and game.get('id'):
                        matching_game.write(
                            {
                                'name': game.get('name'),
                                'url': game.get('url'),
                                'first_release_date': datetime.fromtimestamp(game.get('first_release_date'), tz=None) if game.get('first_release_date') else False,
                                'platform_ids': self.env['igdb.platform'].search([('igdb_id', '=', game.get('platforms'))]).ids,
                                'genre_ids': self.env['igdb.genre'].search([('igdb_id', '=', game.get('genres'))]).ids,
                                'theme_ids': self.env['igdb.theme'].search([('igdb_id', '=', game.get('themes'))]).ids,
                            })
                        matching_games += matching_game
                        game_igc_dict[matching_game] = involved_game_company_ids

                # Todo: move below into a cron to run in the background or multithread somehow, too slow to run here
                # covers_url = 'https://api.igdb.com/v4/covers'
                # covers_list = ", ".join([str(game.get('id')) for game in response_json if game.get('cover') is not None])
                # covers_query = "fields *; where game = (%s); limit 500;" % covers_list
                # covers_response = requests.post(covers_url, headers={'Client-ID': config.client_id_string,
                #                                    'Authorization': 'Bearer ' + config.access_token},
                #                                 data=covers_query)
                # covers_response.raise_for_status()
                # covers_response_json = covers_response.json()
                #
                # for cover in covers_response_json:
                #     game = self.env['igdb.game'].search([('igdb_id', '=', cover.get('game'))])
                #     cover_url = "https://images.igdb.com/igdb/image/upload/t_cover_big/%s.jpeg" % cover.get('image_id')
                #     cover_image_response = requests.get(cover_url)
                #     cover_image_response.raise_for_status()
                #
                #     cover_image_response_content = cover_image_response.content
                #     encoded_cover_image_response_content = base64.b64encode(cover_image_response_content)
                #     game.game_cover = encoded_cover_image_response_content
                #
                #     print("Encoding image %s of %s" % (covers_response_json.index(cover), len(covers_response_json)))

                # Calculate already-retrieved records from the API, to enable retrieving >500 records at once (the limit
                # for a single request).
                retrieved_igdb_ids += [str(rj.get('id')) for rj in response_json]
                retrieved_igdb_ids_str = ", ".join(retrieved_igdb_ids)

                igc_url = 'https://api.igdb.com/v4/involved_companies'

                most_recent_igc_igdb_id = 0
                dict_game_igdb_ids = [str(dict_game.igdb_id) for dict_game in list(game_igc_dict.keys())]  # Get the igdb_ids for each key, i.e. all created and matched games so far this loop

                igc_query_finished = False
                igc_company_dict = {}
                igc_company_dict_inv = defaultdict(list)
                while not igc_query_finished:
                    igc_detailed_query = 'fields *; where game = (%s) & id > %s; sort id asc; limit 500;' % (
                    ",".join(dict_game_igdb_ids), most_recent_igc_igdb_id)
                    igc_response = requests.post(igc_url, headers={'Client-ID': config.client_id_string,
                                                                 'Authorization': 'Bearer ' + config.access_token},
                                             data=igc_detailed_query)
                    igc_response.raise_for_status()
                    igc_response_json = igc_response.json()

                    if len(igc_response_json) == 0:
                        igc_query_finished = True
                        continue

                    new_or_modified_igcs = self.env['igdb.involved.game.company']
                    for igc in igc_response_json:
                        matching_igc = self.env['igdb.involved.game.company'].search(
                            [('igdb_id', '=', igc.get('id'))]) if igc.get('id') else False
                        igc_game = self.env['igdb.game'].search([('igdb_id', '=', igc.get('game'))], limit=1)
                        company_id = igc.get('company')
                        if not matching_igc and igc.get('id'):
                            new_igc = self.env['igdb.involved.game.company'].create({
                                'igdb_id': igc.get('id'),
                                'is_developer': igc.get('developer'),
                                'is_publisher': igc.get('publisher'),
                                'is_porter': igc.get('porter'),
                                'game_id': igc_game.id,
                            })
                            new_or_modified_igcs += new_igc
                            igc_company_dict[new_igc] = company_id
                            igc_company_dict_inv[company_id].append(new_igc)
                        elif matching_igc and igc.get('id'):
                            matching_igc.write({
                                'is_developer': igc.get('developer'),
                                'is_publisher': igc.get('publisher'),
                                'is_porter': igc.get('porter'),
                                'game_id': igc_game.id,
                            })
                            new_or_modified_igcs += matching_igc
                            igc_company_dict[matching_igc] = company_id
                            igc_company_dict_inv[company_id].append(matching_igc)
                    most_recent_igc_igdb_id = new_or_modified_igcs[-1].igdb_id

                company_url = 'https://api.igdb.com/v4/companies'

                most_recent_company_igdb_id = 0
                dict_igc_company_ids = [str(igc_company) for igc_company in set(igc_company_dict.values())]

                company_query_finished = False
                while not company_query_finished:
                    company_detailed_query = 'fields *; where id = (%s) & id > %s; sort id asc; limit 500;' % (",".join(dict_igc_company_ids), most_recent_company_igdb_id)
                    company_response = requests.post(company_url, headers={'Client-ID': config.client_id_string,
                                                                   'Authorization': 'Bearer ' + config.access_token},
                                                 data=company_detailed_query)
                    company_response.raise_for_status()
                    company_response_json = company_response.json()

                    if len(company_response_json) == 0:
                        company_query_finished = True
                        continue

                    new_or_modified_companies = self.env['igdb.game.company']
                    for company in company_response_json:
                        matching_company = self.env['igdb.game.company'].search(
                            [('igdb_id', '=', company.get('id'))]) if company.get('id') else False
                        country_code = COUNTRY_NUMERIC_CODES.get(str(company.get('country')), '')
                        country_rec = self.env['res.country'].search([('code', '=', country_code)]) if country_code else self.env['res.country']
                        if not matching_company and company.get('id'):
                            new_company = self.env['igdb.game.company'].create({
                                'igdb_id': company.get('id'),
                                'url': company.get('url'),
                                'name': company.get('name'),
                                'slug': company.get('slug'),
                                'country_id': country_rec.id,
                                'involved_game_company_ids': [Command.link(igc_rec.id) for igc_rec in igc_company_dict_inv.get(company.get('id'))],
                            })  # Todo: eventually sort out changed_game_company_id, parent_company_id, involved_game_company_ids here
                            new_or_modified_companies += new_company
                        elif matching_company and company.get('id'):
                            matching_company.write({
                                'url': company.get('url'),
                                'name': company.get('name'),
                                'slug': company.get('slug'),
                                'country_id': country_rec.id,
                                'involved_game_company_ids': [Command.link(igc_rec.id) for igc_rec in igc_company_dict_inv.get(company.get('id'))],
                            })  # Todo: eventually sort out changed_game_company_id, parent_company_id, involved_game_company_ids here
                            new_or_modified_companies += matching_company
                    most_recent_company_igdb_id = new_or_modified_companies[-1].igdb_id

            query.result_game_ids = (created_games + matching_games).sorted(key=lambda mg: (mg['name'],
                                                                            mg['igdb_id']))
            query.search_completed = True
            print("Query %s done!" % query.name)

        return

    def copy(self, default=None):
        new_queries = super().copy(default)
        return new_queries

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        return res