extensions = [
    'sphinx.ext.autodoc',
]
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = 'pytoutv'
copyright = '2016, Benjamin Vanheuverzwijn, Philippe Proulx, Simon Marchi'
author = 'Benjamin Vanheuverzwijn, Philippe Proulx, Simon Marchi'
version = '3.0'
release = '3.0'
language = None
exclude_patterns = []
pygments_style = 'sphinx'
todo_include_todos = False
html_theme = 'alabaster'
html_static_path = ['_static']
htmlhelp_basename = 'pytoutvdoc'
html_theme_options = {
    'github_user': 'bvanheu',
    'github_repo': 'pytoutv',
    'github_button': True,
    'github_banner': True,
    'description': '''<strong><em>pytoutv</em></strong> is a Python
                      package and a command-line interface for fetching
                      TOU.TV metadata and media content.''',
}
html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',
        'searchbox.html',
    ]
}
