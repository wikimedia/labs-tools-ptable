# -*- coding: utf-8 -*-
"""
This file is part of the Wikidata periodic table © 2012-2015 by Ricordisamoa.

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
import operator
from urllib import urlencode
from urllib2 import urlopen
from collections import defaultdict

try:
    from functools import ttl_cache
except ImportError:
    from cachetools import ttl_cache

import data


# cachetools does not support maxsize=None
@ttl_cache(maxsize=20, ttl=21600)
def get_json_cached(url, data):
    """The information is cached for 6 hours."""
    return json.load(urlopen(url, data))


def get_json(url, data):
    return get_json_cached(url, urlencode(data))


class ElementProvider(object):
    """Base class for element providers."""

    WD_API = 'http://www.wikidata.org/w/api.php'
    API_LIMIT = 50
    WDQ_API = 'http://wdq.wmflabs.org/api'

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

    def iter_good(self):
        iterator = iter(self)
        while True:
            try:
                yield next(iterator)
            except StopIteration:
                raise

    def get_table(self):
        table = {}
        specials = {}
        elements = []
        incomplete = []
        for element in self.iter_good():
            if element.symbol and element.number and element.period:
                if element.group:
                    if element.period not in table:
                        table[element.period] = {}
                    table[element.period][element.group] = element
                    elements.append(element)
                    continue
                elif element.special:
                    if element.period not in specials:
                        specials[element.period] = {}
                    specials[element.period][element.number] = element
                    elements.append(element)
                    continue
            incomplete.append(element)
        lastnum = -1
        elements.sort(key=operator.attrgetter('number'))
        for pindex, pitem in enumerate(data.periods):
            period = pindex + 1
            if period not in table:
                table[period] = {}
            for gindex, gitem in enumerate(data.groups):
                group = gindex + 1
                if group in table[period]:
                    table[period][group].__class__ = ElementCell  # XXX
                    lastnum += 1
                elif len(elements) > lastnum + 1:
                    last_el = elements[lastnum]
                    next_el = elements[lastnum + 1]
                    if next_el.number - last_el.number == 1:
                        if next_el.special is not None and next_el.special != last_el.special:
                            table[period][group] = IndicatorCell(
                                next_el.special - data.special_start + 1)
                            lastnum += len(specials[next_el.period])
                        else:
                            table[period][group] = EmptyCell()
                    else:
                        table[period][group] = UnknownCell()
                else:
                    table[period][group] = EmptyCell()
        special_series = {}
        for sindex, sitem in enumerate(data.special_series):
            period = sindex + data.special_start
            special_series[sindex] = [IndicatorCell(sindex + 1)]
            if period in specials:
                for i in sorted(specials[period].keys()):
                    specials[period][i].__class__ = ElementCell  # XXX
                    special_series[sindex].append(specials[period][i])
        return elements, table, special_series, incomplete


class WdqElementProvider(ElementProvider):
    """Load elements from Wikidata Query."""
    def __iter__(self):
        wdq = self.get_wdq()
        ids = ['Q%d' % item_id for item_id in wdq['items']]
        entities = self.get_entities(ids, props='labels',
                                     languages=self.language, languagefallback=1)
        elements = defaultdict(Element)
        subclass_of = defaultdict(list)
        wdq['props'] = defaultdict(list, wdq.get('props', {}))
        for item_id, datatype, value in wdq['props'][str(Element.number_pid)]:
            if datatype != 'quantity':
                continue
            value = value.split('|')
            if len(value) == 4:
                value = map(float, value)
                if len(set(value[:3])) == 1 and value[3] == 1 and value[0] == int(value[0]):
                    elements[item_id].number = int(value[0])
        for item_id, datatype, value in wdq['props'][str(Element.symbol_pid)]:
            if datatype != 'string':
                continue
            elements[item_id].symbol = value
        for item_id, datatype, value in wdq['props'][str(Element.subclass_pid)]:
            if datatype != 'item':
                continue
            subclass_of[item_id].append(value)
        for item_id, element in elements.items():
            element.item_id = 'Q%d' % item_id
            for prop in ('number', 'symbol'):
                if not hasattr(element, prop):
                    setattr(element, prop, None)
            element.load_data_from_superclasses(subclass_of[item_id])
            label = None
            entity = entities.get(element.item_id)
            if entity and 'labels' in entity and len(entity['labels']) == 1:
                label = entity['labels'].values()[0]['value']
            element.label = label
            yield element

    @classmethod
    def get_wdq(cls):
        pids = [str(getattr(Element, name))
                for name in ('symbol_pid', 'subclass_pid', 'number_pid')]
        query = {
            'q': 'claim[%d]' % Element.symbol_pid,
            'props': ','.join(pids)
        }
        return get_json(cls.WDQ_API, query)


class ApiElementProvider(ElementProvider):
    """Load elements from the Wikidata API."""
    def __iter__(self):
        ids = self.get_elements_titles()
        entities = self.get_entities(ids, props='labels|claims',
                                     languages=self.language, languagefallback=1)
        for item_id, item in entities.items():
            try:
                element = self.factory(item)
            except Exception:
                # FIXME
                continue
            else:
                yield element

    @staticmethod
    def get_claim_value(claim):
        return claim['mainsnak']['datavalue']['value']

    @classmethod
    def factory(cls, entity):
        claims = defaultdict(list, entity.get('claims', []))
        try:
            number = int(cls.get_claim_value(claims['P%d' % Element.number_pid][0])['amount'])
        except IndexError:
            number = None
        try:
            symbol = cls.get_claim_value(claims['P%d' % Element.symbol_pid][0])
        except IndexError:
            symbol = None
        if 'labels' in entity and len(entity['labels']) == 1:
            label = entity['labels'].values()[0]['value']
        else:
            label = None
        element = Element(number=number, symbol=symbol, item_id=entity['id'], label=label)
        element.load_data_from_superclasses(cls.get_claim_value(claim)['numeric-id']
                                            for claim in claims['P%d' % Element.subclass_pid])
        return element

    @classmethod
    def get_elements_titles(cls):
        """
        Get titles of Wikidata items of chemical elements.

        All items that link to Element.symbol_pid are considered chemical elements.
        """
        backlinks_query = {
            'action': 'query',
            'format': 'json',
            'generator': 'backlinks',
            'gblnamespace': 0,
            'gbllimit': 'max',
            'gbltitle': 'Property:P%d' % Element.symbol_pid,
            'gblfilterredir': 'nonredirects',
            'prop': ''
        }
        backlinks = get_json(cls.WD_API, backlinks_query)
        return [page['title'] for page in backlinks['query']['pages'].values()]


class PropertyAlreadySetException(Exception):
    """Property already set."""


class Element(object):

    props = ('number', 'symbol', 'item_id', 'label', 'period', 'group', 'special')
    symbol_pid = 246
    subclass_pid = 279
    discovery_pid = 575
    number_pid = 1086

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            if key in self.props:
                setattr(self, key, val)
        self.classes = []

    def load_data_from_superclasses(self, targets):
        period = None
        group = None
        special = None
        for target in targets:
            if target in data.periods:
                period = data.periods.index(target) + 1
            elif target in data.groups:
                group = data.groups.index(target) + 1
            elif target in data.special_series:
                special = data.special_series.index(target) + data.special_start
            if target in data.special_subclasses:
                self.classes.append(data.special_subclasses[target])
        self.period = period
        self.group = group
        self.special = special

    def __setattr__(self, key, value):
        if (key in self.props and hasattr(self, key) and
                getattr(self, key) is not None and getattr(self, key) != value):
            raise PropertyAlreadySetException
        super(Element, self).__setattr__(key, value)

    def __iter__(self):
        for key in self.props:
            yield (key, getattr(self, key))


class TableCell(object):
    """A table cell."""


class ElementCell(Element, TableCell):
    """An element cell."""


class IndicatorCell(TableCell):
    """An indicator cell."""
    def __init__(self, index):
        self.index = index


class UnknownCell(TableCell):
    """An unknown cell."""


class EmptyCell(TableCell):
    """An empty cell."""
