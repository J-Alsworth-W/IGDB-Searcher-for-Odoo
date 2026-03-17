{
    'name': 'IGDB Searcher',
    'version': '0.1',
    'sequence': 100,
    'summary': 'Search the IGDB site using its API to retrieve game information via more powerful search tools',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/igdb_query_views.xml',
        'views/igdb_platform_views.xml',
        'views/igdb_game_views.xml',
        'views/igdb_genre_views.xml',
        'views/igdb_theme_views.xml',
        'views/igdb_config_views.xml',
        'views/igdb_menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'author': 'Jacob Alsworth',
    'license': 'GPL-3',
}