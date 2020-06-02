# -*- coding: utf-8 -*-
"""
Copyright © 2012-2016 Ricordisamoa

This file is part of the Wikidata periodic table.

The Wikidata periodic table is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The Wikidata periodic table is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with the Wikidata periodic table.  If not, see <http://www.gnu.org/licenses/>.
"""

import json
from urllib.parse import urlencode
from urllib.request import urlopen

from cachetools.func import ttl_cache


@ttl_cache(maxsize=200, ttl=21600)
def get_json_cached(url, data, get):
    """The information is cached for 6 hours."""
    if get:
        params = ['{0}?{1}'.format(url, data)]
    else:
        params = [url, data.encode('utf-8')]
    with urlopen(*params) as response:
        raw = response.read()
    return json.loads(raw.decode('utf-8'))


def get_json(url, data, get=False):
    """Wrapper for get_json_cached() with URL encoding."""
    return get_json_cached(url, urlencode(data), get)


class PropertyAlreadySetException(Exception):
    """Property already set."""


class TableCell:
    """A table cell."""


class BaseProvider:
    """Base class for all providers."""

    WD_API = 'https://www.wikidata.org/w/api.php'
    API_LIMIT = 50

    def __init__(self, language):
        self.language = language

    @classmethod
    def get_available_languages(cls):
        query = dict(action='query', format='json', meta='siteinfo', siprop='languages')
        result = get_json(cls.WD_API, query).get('query', {}).get('languages', [])
        return [lang['code'] for lang in result]

    @classmethod
    def get_entities(cls, ids, **kwargs):
        entities = {}
        query = dict(action='wbgetentities', format='json', **kwargs)
        for index in range(0, len(ids), cls.API_LIMIT):
            query['ids'] = '|'.join(ids[index:index + cls.API_LIMIT])
            new_entities = get_json(cls.WD_API, query).get('entities', {})
            entities.update(new_entities)
        return entities

    def get_table(self):
        raise NotImplementedError()


class SparqlBase:
    """Load items from Wikidata SPARQL query service."""

    SPARQL_API = 'https://query.wikidata.org/sparql'

    @classmethod
    def get_sparql(cls, query):
        response = get_json(cls.SPARQL_API, {'query': query, 'format': 'json'}, get=True)
        return response['results']['bindings']
