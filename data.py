# -*- coding: utf-8 -*-
"""
Copyright © 2012-2015 Ricordisamoa

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

# mappings of period and group numbers to Wikidata item ids
# TODO: json?
periods = [
    191936,
    207712,
    211331,
    239825,
    244982,
    239813,
    244979,
    428818,
    986218
]
groups = [
    10801007,
    19563,
    108307,
    189302,
    193276,
    193280,
    202602,
    202224,
    208107,
    205253,
    185870,
    191875,
    189294,
    106693,
    106675,
    104567,
    19605,
    19609
]
special_start = 6
special_series = [
    19569,  # lanthanide
    19577,  # actinide
    428874  # superactinide
]

special_subclasses = {
    19557: 'alkali-metal',
    19591: 'post-transition-metal',
    19596: 'metalloid',
    19753344: 'diatomic-nonmetal',
    19753345: 'polyatomic-nonmetal'
}
