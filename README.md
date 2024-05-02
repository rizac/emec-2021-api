# emec_2021_restful_api

Deploy instructions

Got to /www/data (or whatever directory):

```commandline
git clone https://github.com/rizac/emec-2021-api.git ./emec-2021-api && cd ./emec-2021-api
python3 -m venv .env
source .env/bin/activate
pip install --upgrade pip setuptools && pip install -r ./requirements.txt && pip install gunicorn
```


Run gunicorn:

https://flask.palletsprojects.com/en/3.0.x/deploying/gunicorn/
https://docs.gunicorn.org/en/stable/run.html


```commandline
gunicorn -w 4 -b 127.0.0.1:8000 'gunicorn:app'
```

kill gunicorn (https://stackoverflow.com/questions/14604653/how-to-stop-gunicorn-properly):

```commandline
pkill gunicorn
```

Configure apache:

https://flask.palletsprojects.com/en/3.0.x/deploying/apache-httpd/


```
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so
ProxyPass /fdsnws/events/1/query http://127.0.0.1:8000/
RequestHeader set X-Forwarded-Proto http
RequestHeader set X-Forwarded-Prefix /
```