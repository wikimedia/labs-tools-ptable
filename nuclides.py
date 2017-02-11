# -*- coding: utf-8 -*-
"""
Copyright © 2015, 2016 ArthurPSmith
Copyright © 2016-2017 Ricordisamoa

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

import operator
from collections import defaultdict

from base import BaseProvider, SparqlBase, PropertyAlreadySetException, TableCell
from units import time_in_seconds


class NuclideProvider(BaseProvider):
    """Base class for nuclide providers."""

    def get_table(self):
        table = {}
        nuclides = []
        incomplete = []
        lastanum = -1
        lastnnum = -1
        for nuclide in self.iter_good():
            if nuclide.atomic_number is not None and nuclide.neutron_number is not None:
                if nuclide.atomic_number > lastanum:
                    lastanum = nuclide.atomic_number
                if nuclide.neutron_number > lastnnum:
                    lastnnum = nuclide.neutron_number
                if nuclide.atomic_number not in table:
                    table[nuclide.atomic_number] = {}
                table[nuclide.atomic_number][nuclide.neutron_number] = nuclide
                nuclides.append(nuclide)
            else:
                incomplete.append(nuclide)
        nuclides.sort(key=operator.attrgetter('atomic_number', 'neutron_number'))
        for anum in range(0, lastanum+1):
            if anum not in table:
                table[anum] = {}
            for nnum in range(0, lastnnum+1):
                if nnum in table[anum]:
                    table[anum][nnum].__class__ = NuclideCell
                else:
                    table[anum][nnum] = NoneCell()

        return nuclides, table, incomplete

    def decorate_by_halflife(self, nuclides):
        half_life_map = {
            1.0e9: 'hl1e9',
            1.0e6: 'hl1e6',
            1.0e3: 'hl1e3',
            1.0e2: 'hl1e2',
            1.0e1: 'hl1e1',
            1.0: 'hl1e0',
            1.0e-1: 'hl1e-1',
            1.0e-2: 'hl1e-2',
            1.0e-3: 'hl1e-3',
            1.0e-6: 'hl1e-6',
            1.0e-9: 'hl1e-9',
            1.0e-12: 'hl1e-12',
            1.0e-15: 'hl1e-15',
            1.0e-18: 'hl1e-18',
            0: 'hl1e-21'}
        for nuclide in nuclides:
            half_life = nuclide.half_life
            if half_life is not None:
                for hl_limit in sorted(half_life_map, reverse=True):
                    if (half_life >= hl_limit):
                        hl_class = half_life_map[hl_limit]
                        break
                if hl_class is None:
                    hl_class = half_life_map[0]  # default value
                nuclide.classes.append(hl_class)

    def decorate_by_decay_mode(self, nuclides):
        decay_modes_map = {
            '14646001': 'beta-minus',
            '18907407': 'double-beta',
            '1357356': 'positron-emission',
            '109910': 'electron-capture',
            '520827': 'double-electron-capture',
            '179856': 'alpha-decay',
            '898923': 'neutron-emission',
            '902157': 'proton-emission',
            '9253686': 'two-proton-emission',
            '21457313': 'three-proton-emission',
            '21456752': 'two-neutron-emission',
            '21457084': 'three-neutron-emission',
            '21457201': 'four-neutron emission',
            '21457421': 'double-alpha-decay',
            '146682': 'spontaneous-fission'
        }
        for nuclide in nuclides:
            decay_modes = nuclide.decay_modes
            if len(decay_modes) > 0:
                dm = decay_modes[0]
                if str(dm) in decay_modes_map:
                    nuclide.classes.append(decay_modes_map[str(dm)])


class SparqlNuclideProvider(SparqlBase, NuclideProvider):
    """Load nuclide info from Wikidata Sparql endpoint."""
    def __iter__(self):
        nuclides = defaultdict(Nuclide)
        nuclides_query = "SELECT ?nuclide ?atomic_number ?neutron_number ?stable ?label WHERE {{ \
    ?nuclide wdt:P{0}/wdt:P{1}* wd:Q{2} ; \
             wdt:P{3} ?atomic_number ; \
             wdt:P{4} ?neutron_number ; \
             rdfs:label ?label ; \
    FILTER NOT EXISTS {{ ?nuclide wdt:P{0} wd:Q{5} . }} \
    FILTER(lang(?label) = 'en') \
    BIND( EXISTS {{ ?nuclide wdt:P{0} wd:Q{6} . }} AS ?stable ) \
}}".format(Nuclide.instance_pid, Nuclide.subclass_pid, Nuclide.isotope_qid,
            Nuclide.atomic_number_pid, Nuclide.neutron_number_pid,
            Nuclide.isomer_qid, Nuclide.stable_qid)
        query_result = self.get_sparql(nuclides_query)
        for nuclide_result in query_result:
            nuclide_uri = nuclide_result['nuclide']['value']
            atomic_number = nuclide_result['atomic_number']['value']
            neutron_number = nuclide_result['neutron_number']['value']
            label = nuclide_result['label']['value']
            nuclides[nuclide_uri].atomic_number = int(atomic_number)
            nuclides[nuclide_uri].neutron_number = int(neutron_number)
            nuclides[nuclide_uri].label = label
            nuclides[nuclide_uri].half_life = None
            nuclides[nuclide_uri].item_id = nuclide_uri.split('/')[-1]
            if nuclide_result['stable']['value'] == 'true':
                nuclides[nuclide_uri].classes.append('stable')

        hl_query = "SELECT ?nuclide ?half_life ?half_life_unit WHERE {{ \
    ?nuclide wdt:P{0}/wdt:P{1}* wd:Q{2} ; \
             p:P{3} ?hl_statement . \
    ?hl_statement psv:P{3} ?hl_value . \
    ?hl_value wikibase:quantityAmount ?half_life ; \
              wikibase:quantityUnit ?half_life_unit . \
}}".format(Nuclide.instance_pid, Nuclide.subclass_pid, Nuclide.isotope_qid,
            Nuclide.half_life_pid)

        query_result = self.get_sparql(hl_query)
        for nuclide_result in query_result:
            nuclide_uri = nuclide_result['nuclide']['value']
            if nuclide_result['half_life']['value'] == '0':
                continue  # WDQS bug: values sometimes zero - skip
            if nuclide_uri in nuclides:
                if nuclides[nuclide_uri].half_life is None:
                    nuclides[nuclide_uri].half_life = time_in_seconds(
                        nuclide_result['half_life']['value'],
                        nuclide_result['half_life_unit']['value'])
                # else - sparql returned more than 1 half-life value - problem?

        decay_query = "SELECT ?nuclide ?decay_to ?decay_mode ?fraction WHERE {{ \
    ?nuclide wdt:P{0}/wdt:P{1}* wd:Q{2} ; \
             p:P{3} ?decay_statement . \
    ?decay_statement ps:P{3} ?decay_to ; \
                     pq:P{4} ?decay_mode ; \
                     pq:P{5} ?fraction . \
}}".format(Nuclide.instance_pid, Nuclide.subclass_pid, Nuclide.isotope_qid,
            Nuclide.decays_to_pid, Nuclide.decay_mode_pid, Nuclide.proportion_pid)
        query_result = self.get_sparql(decay_query)
        for nuclide_result in query_result:
            nuclide_uri = nuclide_result['nuclide']['value']
            if nuclide_uri in nuclides:
                decay_mode_uri = nuclide_result['decay_mode']['value']
                decay_mode = int(decay_mode_uri.split('/')[-1].replace('Q', ''))
                nuclides[nuclide_uri].decay_modes.append(decay_mode)

        for item_id, nuclide in nuclides.items():
            yield nuclide

    def get_magic_numbers(self):
        magic_query = "SELECT ?magic_number WHERE {{ \
    ?number wdt:P{0} wd:Q{1} ; \
            wdt:P{2} ?magic_number . \
}} ORDER by ?magic_number".format(Nuclide.instance_pid, Nuclide.magic_qid,
                                  Nuclide.numeric_pid)
        query_result = self.get_sparql(magic_query)
        magic_numbers = []
        for magic_result in query_result:
            magic_number = magic_result['magic_number']['value']
            magic_numbers.append(int(magic_number))
        return magic_numbers


class Nuclide:

    props = ('atomic_number', 'neutron_number', 'item_id', 'label', 'half_life', 'decay_modes')
    atomic_number_pid = 1086
    neutron_number_pid = 1148
    half_life_pid = 2114
    decays_to_pid = 816
    decay_mode_pid = 817
    proportion_pid = 1107
    instance_pid = 31
    subclass_pid = 279
    isotope_qid = 25276  # top-level class under which all isotopes to be found
    stable_qid = 878130  # id for stable isotope
    isomer_qid = 846110  # metastable isomers all instances of this
    magic_qid = 11606  # magic number of nucleons for stability
    numeric_pid = 1181

    def __init__(self, **kwargs):
        self.decay_modes = []
        for key, val in kwargs.items():
            if key in self.props:
                setattr(self, key, val)
        self.classes = []

    def __setattr__(self, key, value):
        if (key in self.props and hasattr(self, key) and
                getattr(self, key) is not None and getattr(self, key) != value):
            raise PropertyAlreadySetException
        super(Nuclide, self).__setattr__(key, value)

    def __iter__(self):
        for key in self.props:
            yield (key, getattr(self, key))


class NuclideCell(Nuclide, TableCell):
    """A nuclide cell."""


class NoneCell(TableCell):
    """An empty cell."""
