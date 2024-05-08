# EMEC 2021 API

FDSN web API serving data of the
[European-Mediterranean Earthquake Catalogue – Version 2021](https://gfzpublic.gfz-potsdam.de/pubman/item/item_5023147)

This page covers the installation of the API in a production server.
Apache2 will be configured as reverse proxy server forwarding 
all requests to `[site_url]/fdsnws/event/1/query` to a Gunicorn server
running in Python that will process and return the requested seismic events 
in QuakeML or text format.

**Important notes**

  We assume that no other site is enabled and configured on the server. 
  Because this is most likely not the case, please check the notes in the
  Apache configuration section of this document


## Install package

Got to `/var/www` and clone the project:

```commandline
git clone https://github.com/rizac/emec-2021-api.git ./emec-2021-api && cd ./emec-2021-api
python3 -m venv .env
source .env/bin/activate
pip install --upgrade pip setuptools && pip install -r ./requirements.txt && pip install gunicorn
```

**Important notes**
- You can clone the project everywhere you want, but if you do not choose
  `var/www` then you will need to modify all scripts in the examples below

## Run Python server (gunicorn):

Gunicorn is a pure-Python HTTP server for WSGI applications. We will first install
and run Gunicorn and then configure apache to proxy pass specific url to gunicorn.

Let's run gunicorn as Unix service located at:

`/etc/systemd/system/emec-2021-api.service`

And copy in it the content below:

```
[Unit]
Description=Gunicorn instance to serve the EMEC FDSN Event API
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/emec-2021-api
Environment="PATH=/var/www/emec-2021-api/.env/bin"
ExecStart=/var/www/emec-2021-api/.env/bin/gunicorn --workers 3 --bind 127.0.0.1:8001 -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

**Important notes** 
- it is recommended to run the service as sub-user without root permissions
in case change the `User` below but also the ownership of the whole emec-2021 Python
directory
- The `bind` value (`--bind 127.0.0.1:8001`) must be the same in the apache config 
 (see later)

Enable the service:
```commandline
sudo systemctl enable emec-2021-api
```

### (Re)start service:

Service file modified? (otherwise skip this step. 
You will be warned on the terminal later in any case, if needed):
```commandline
systemctl daemon-reload
```

Restart the service:
```commandline
pkill -f /var/www/emec-2021-api; systemctl restart emec-2021-api
```
(the first part kills all running processes in this example
all processes whose command line matches "/var/www/emec-2021-api")


### Check  service:

```commandline
sudo systemctl status emec-2021-api
```
You should see something like:
```commandline
● emec-2021-api.service - Gunicorn instance to serve myproject
     Loaded: loaded (/etc/systemd/system/emec-2021-api.service; enabled; vendor preset: enabled)
     Active: active (running) since Thu 2024-05-02 13:45:39 CEST; 19s ago
   Main PID: 1493308 (gunicorn)
      Tasks: 13 (limit: 9366)
     Memory: 151.7M
        CPU: 1.444s
```


<details>

<summary>Quick test via the command line</summary>

```commandline
gunicorn -w 4 -b 127.0.0.1:8001 wsgi:app
```

kill gunicorn (https://stackoverflow.com/questions/14604653/how-to-stop-gunicorn-properly)
```commandline
pkill gunicorn
```

</details>

**References**

  - https://flask.palletsprojects.com/en/3.0.x/deploying/gunicorn/
  - https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04
  - https://docs.gunicorn.org/en/stable/run.html


## Configure Apache to forward requests to the Gunicorn server

Save this content inside `/etc/apache2/sites-available/emec-2021-api.conf`
(see notes below):

```
<VirtualHost *:80>
    LoadModule proxy_module /usr/lib/apache2/modules/mod_proxy.so
    LoadModule proxy_http_module /usr/lib/apache2/modules/mod_proxy_http.so
    ProxyPass /fdsnws/event/1/query http://127.0.0.1:8001/
    RequestHeader set X-Forwarded-Proto http
    RequestHeader set X-Forwarded-Prefix /
</VirtualHost>
```

**Important notes** 

- **check** that all `LoadModule`s point to an existing path, in the example
  above `/usr/lib/apache2/modules/` 
- **The example above works if no other site is enabled and configured. Because 
  this is most likely not the case, then you will probably put the 
  instructions above (at least the first three lines of text) 
  in your existing config, instead of creating a new
  file**

### Test apache:

```commandline
(cd /etc/apache2 && apache2ctl configtest)
```

<details>
<summary> click in case of Invalid command 'RequestHeader' error</summary>

```commandline
sudo a2enmod headers
```

and then restart apache:

```commandline
systemctl restart apache2  
# or service apache2 restart, depending on your installation
```
Ref: - https://www.brandcrock.com/how-to-fix-invalid-command-requestheader-in-the-server-configuration/
</details>

**References**

- https://flask.palletsprojects.com/en/3.0.x/deploying/apache-httpd/


## Maintenance

To update the source code (bugfix, update catalog):

 - `cd /var/www/emec-2021-api` (or wherever the source code is) and `git pull`
 - If you want to update the catalog, **activate virtualenv** (see above) and then:
   ```commandline
   python emec_2021/emec.py
   ```
  - restart gunicorn (see above) 
  - restart apache (see above)