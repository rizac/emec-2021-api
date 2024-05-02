from emec_2021.flaskapp import app

# we assume the app is run with gunicorn behind a proxy
# (https://flask.palletsprojects.com/en/3.0.x/deploying/proxy_fix/):
from werkzeug.middleware.proxy_fix import ProxyFix

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
