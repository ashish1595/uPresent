import json
import ssl
import urllib.request
import http.client
import mimetypes
import logging
from flask import current_app, jsonify


log = logging.getLogger('root')


def obtain_token():
    log.info("Trying to obtain token from vault ---->>")
    context = ssl._create_unverified_context()
    context.load_cert_chain(
        current_app.config['VAULT_CLIENT_CERT'], current_app.config['VAULT_CLIENT_KEY'])
    conn = http.client.HTTPSConnection(
        current_app.config['VAULT_HOSTNAME'], port=current_app.config['VAULT_PORT'], context=context)
    payload = "{\r\n\t\"name\": \"attendance\"\r\n}"
    headers = {
        'Content-Type': 'application/json'
    }
    conn.request(
        "POST", current_app.config['VAULT_LOGIN_URL'], payload, headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode('utf8')).get("auth").get("client_token")


def obtain_data():
    log.info("Trying to obtain secrets from vault ---->>")
    secrets = obtain_token()
    url = "https://" + current_app.config['VAULT_HOSTNAME'] + ":" + \
        str(current_app.config['VAULT_PORT']) + \
        current_app.config['VAULT_DATA_URL']
    hdr = {'X-Vault-Token': secrets}
    gcontext = ssl.SSLContext()
    req = urllib.request.Request(
        url, headers=hdr, method='GET')
    response = urllib.request.urlopen(req, context=gcontext)
    data = json.loads(
        response.read().decode('utf8')).get("data").get("data")
    return data
