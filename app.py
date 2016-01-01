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

from flask import Flask, request, jsonify, render_template, send_file
from flask.json import JSONEncoder

import chemistry


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (chemistry.Element, chemistry.TableCell)):
            return obj.__dict__
        return super(CustomJSONEncoder, self).default(obj)


app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

# May be set to chemistry.ApiElementProvider (slower, but more up-to-date)
element_provider_class = chemistry.WdqElementProvider

fake_globals = {'isinstance': isinstance}
for key in ('EmptyCell', 'UnknownCell', 'ElementCell', 'IndicatorCell'):
    fake_globals[key] = getattr(chemistry, key)


@app.before_request
def set_language():
    app.language = request.args.get('lang')
    if not app.language:
        available_languages = element_provider_class.get_available_languages()
        app.language = request.accept_languages.best_match(available_languages)
    if not app.language:
        app.language = 'en'
    app.element_provider = element_provider_class(app.language)


@app.route('/')
def index():
    """Render the index page."""
    elements, table, special_series, incomplete = app.element_provider.get_table()
    return render_template('index.html', table=table, special_series=special_series,
                           incomplete=incomplete, **fake_globals)


@app.route('/license')
def license():
    """Render the license page."""
    return render_template('license.html')


@app.route('/license/full')
def license_full():
    """Send the full GPL license."""
    return send_file('COPYING', mimetype='text/plain', as_attachment=False)


@app.route('/api')
def api():
    """Render the API result if appropriate, otherwise render the API documentation page."""
    props = request.args.getlist('props')
    if props:
        elements, table, special_series, incomplete = app.element_provider.get_table()
        result = {'elements': elements, 'incomplete': incomplete}
        available_props = set(props).intersection(set(result.keys()))
        result = {prop: result[prop] for prop in available_props}
        return jsonify(result)
    return render_template('api.html')


if __name__ == '__main__':
    app.run()
