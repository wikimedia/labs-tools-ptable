# -*- coding: utf-8 -*-
"""
Copyright © 2015 ArthurPSmith

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

# time units and their values in multiples of seconds
time_units = {
    11574: 1.0,          # second
    7727: 60.0,          # minute
    25235: 3600.0,       # hour
    573: 86400.0,        # day
    23387: 604800.0,     # week
    5151: 2.630e6,       # month (average)
    1092296: 3.156e7,    # year (annum)
    577: 3.156e7,        # year (calendar)
    723733: 1.0e-3,      # millisecond
    842015: 1.0e-6,      # microsecond
    838801: 1.0e-9,      # nanosecond
    3902709: 1.0e-12,    # picosecond
    1777507: 1.0e-15,    # femtosecond
    2483628: 1.0e-18     # attosecond
}


def time_in_seconds(amount_str, unit_uri):
    amount = float(amount_str)
    unit_id = int(unit_uri.split('/')[-1].replace('Q', ''))
    amount *= time_units[unit_id]
    return amount
