from odoo import api, exceptions, fields, models, modules, _
import requests
import re
from datetime import date, datetime
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
    result_game_ids = fields.Many2many(string="Returned Games", comodel_name='igdb.game',
                                       relation="igdb_query_res_games_rel", copy=False)
    release_date_start = fields.Date(string="Initial Release Date (Start)")
    release_date_end = fields.Date(string="Initial Release Date (End)")
    search_completed = fields.Boolean(string="Search Completed", default=False, copy=False)
    where_clause_used = fields.Boolean(compute='_compute_concatenated_query')
    # Todo: Add developers and publishers as their own model types here, as well as player perspective.

    @api.depends('included_platform_ids', 'excluded_platform_ids', 'game_name', 'release_date_start', 'release_date_end')
    def _compute_concatenated_query(self):
        for query in self:
            where_clause_used = False

            concat_query = "fields *;"
            if query.game_name:
                concat_query += ' search "%s";' % query.game_name

            if query.included_platform_ids or query.excluded_platform_ids:
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

            concat_query += " & id != (); limit 500;" if where_clause_used else " id != (); limit 500;"
            query.concatenated_query = concat_query if concat_query != "fields *;" else ""
            query.where_clause_used = where_clause_used

    @api.constrains('release_date_start', 'release_date_end')
    def _check_dates(self):
        for query in self:
            if query.release_date_end and query.release_date_start > query.release_date_end:
                raise exceptions.ValidationError("The start date (%s) of the search must be earlier than the end date "
                                                 "(%s)."  % (query.release_date_start, query.release_date_end))

    def do_search(self):
        config = self.env['igdb.config'].get_config()
        config.test_connection()

        for query in self:
            games_url = 'https://api.igdb.com/v4/games'
            query_finished = False

            retrieved_igdb_ids = []
            retrieved_igdb_ids_str = ""
            igdb_replacement_regex = r"& id != \(.*\)\w*" if query.where_clause_used else r"id != \(.*\)\w*"

            created_games = self.env['igdb.game']
            matching_games = self.env['igdb.game']

            while not query_finished:
                # If 2nd+ iteration
                if retrieved_igdb_ids_str:
                    where_clause_str = " &" if query.where_clause_used else " where"
                    game_reference = "id" if query.game_name else "id"
                    new_ids_search_str = where_clause_str + " %s != (%s)" % (game_reference, retrieved_igdb_ids_str)

                    detailed_query = re.sub(igdb_replacement_regex, new_ids_search_str,
                                            query.concatenated_query)
                # If 1st iteration
                else:
                    if query.where_clause_used:
                        detailed_query = re.sub(igdb_replacement_regex, retrieved_igdb_ids_str,
                                                query.concatenated_query)
                    else:
                        detailed_query = re.sub(igdb_replacement_regex + ";", retrieved_igdb_ids_str,
                                                query.concatenated_query)

                response = requests.post(games_url, headers={'Client-ID': config.client_id_string,
                                                       'Authorization': 'Bearer ' + config.access_token},
                                         data=detailed_query)
                response.raise_for_status()
                response_json = response.json()

                # The 2nd clause here is to address a bug in the API where despite the detailed_query specifically
                # excluding results with matching IDs, they will still be retrieved by the request anyway.
                if len(response_json) == 0 or retrieved_igdb_ids and query.game_name and retrieved_igdb_ids == [str(game.get('id')) for game in response_json]:  # Todo: unsure if buggy if >500 results, may infinitely loop
                    query_finished = True
                    continue
                for game in response_json:
                    matching_game = self.env['igdb.game'].search(
                        [('igdb_id', '=', game.get('id'))]) if game.get('id') else False
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