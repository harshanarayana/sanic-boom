# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.coverage',
    'sphinx.ext.doctest',
    'sphinx.ext.extlinks',
    'sphinx.ext.ifconfig',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx.ext.mathjax',
]
if os.getenv('SPELLCHECK'):
    extensions += 'sphinxcontrib.spelling',
    spelling_show_suggestions = True
    spelling_lang = 'en_US'

source_suffix = '.rst'
master_doc = 'index'
project = 'sanic-boom'
year = '2018'
author = 'Richard Kuesters'
copyright = '{0}, {1}'.format(year, author)
version = release = '0.1.2'

pygments_style = 'default'
templates_path = ['.']
extlinks = {
    'issue': ('https://github.com/vltr/sanic-boom/issues/%s', '#'),
    'pr': ('https://github.com/vltr/sanic-boom/pull/%s', 'PR #'),
}
# on_rtd is whether we are on readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only set the theme if we're building docs locally
    html_theme = 'sphinx_rtd_theme'

# html_logo = "static/sanic-boom-logo.svg"
html_use_smartypants = True
html_last_updated_fmt = '%b %d, %Y'
html_split_index = False
html_sidebars = {
    '**': ['searchbox.html', 'globaltoc.html', 'sourcelink.html'],
}
html_short_title = '%s-%s' % (project, version)

html_theme_options = {
    "style_external_links": False,
    "logo_only": False,
}

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False
