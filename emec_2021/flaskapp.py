from flask import Flask, request, send_file
import pandas as pd

from emec_2021.emec import create_catalog
from emec_2021.fdsn import apply_query_param, to_xml, to_text, validate_param, Param

app = Flask('emec-2021-api')


_catalog: pd.DataFrame = None  # noqa


def get_catalog():
    global _catalog
    if _catalog is None:
        _catalog = create_catalog()
    return _catalog


@app.route("/", methods=['GET', 'POST'])
def get_events():
    print('ok')
    catalog = get_catalog()
    params = request.args
    method = to_xml
    mimetype = 'text/xml'
    try:
        for prm in params:
            try:
                param, value = validate_param(prm, params.getlist(prm)[-1])
            except ValueError as err:
                return str(err), 400
            if param == Param.format and value == 'text':
                mimetype = 'text/plain'
                method = to_text
                continue
            catalog = apply_query_param(catalog, param, value)
        return send_file(method(catalog), as_attachment=False, mimetype=mimetype)
    except Exception as exc:
        return str(exc), 500


if __name__ == "__main__":
    app.run(debug=True)
