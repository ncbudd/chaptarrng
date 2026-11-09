"""Exercise real HTTP startup and cookie-bound UI credentials on disposable data."""
import argparse
import base64
import http.client
import json
import os
from pathlib import Path
import signal
import secrets
import socket
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dotnet', default='dotnet')
parser.add_argument('--app', type=Path, required=True)
parser.add_argument('--log', type=Path, required=True)
parser.add_argument('--misconfigured-oidc', action='store_true')
args = parser.parse_args()
with tempfile.TemporaryDirectory(prefix='chaptarr-audit-startup-') as temporary:
    data = Path(temporary)
    data.chmod(0o700)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    master = secrets.token_hex(16)
    method = 'Oidc' if args.misconfigured_oidc else 'None'
    (data/'config.xml').write_text(f'<Config><ApiKey>{master}</ApiKey><BindAddress>127.0.0.1</BindAddress><Port>{port}</Port><AuthenticationMethod>{method}</AuthenticationMethod><AuthenticationRequired>DisabledForLocalAddresses</AuthenticationRequired><LaunchBrowser>False</LaunchBrowser><AnalyticsEnabled>False</AnalyticsEnabled><UpdateAutomatically>False</UpdateAutomatically></Config>')
    env = dict(os.environ, DOTNET_GCHeapHardLimit='0x30000000', ASPNETCORE_ENVIRONMENT='Production')
    log = open(args.log, 'w')
    process = subprocess.Popen([args.dotnet, str(args.app.resolve()), '-data='+str(data), '-nobrowser', '-nosingleinstancecheck'], stdout=log, stderr=subprocess.STDOUT, env=env)
    def request(path, headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
        connection.request('GET',path,headers=headers or {})
        response=connection.getresponse()
        result=(response.status,dict(response.getheaders()),response.read())
        connection.close()
        return result
    try:
        deadline=time.monotonic()+60
        while time.monotonic()<deadline:
            if process.poll() is not None: raise RuntimeError('App exited during startup; see private smoke log')
            try:
                status,headers,body=request('/initialize.json')
                break
            except (ConnectionError,OSError): time.sleep(0.3)
        else: raise RuntimeError('App did not listen before startup deadline')
        assert status==401,(status,body[:200])
        assert request('/api/v1/system/status')[0]==401
        if args.misconfigured_oidc:
            assert not (data/'setup-token').exists()
            recovery_headers = {'X-Api-Key': master}
        else:
            assert headers.get('WWW-Authenticate','').startswith('Basic realm=')
            token=(data/'setup-token').read_text()
            assert (data/'setup-token').stat().st_mode & 0o777 == 0o600
            authorization='Basic '+base64.b64encode(('setup:'+token).encode()).decode()
            recovery_headers = {'Authorization': authorization}
        status,headers,body=request('/initialize.json',recovery_headers)
        assert status==200,(status,body[:200])
        ui=json.loads(body)['apiKey']
        assert ui.startswith('ui_') and ui!=master
        cookie=headers['Set-Cookie'].split(';',1)[0]
        assert 'httponly' in headers['Set-Cookie'].lower() and 'samesite=strict' in headers['Set-Cookie'].lower()
        assert request('/api/v1/system/status',{'X-Api-Key':ui})[0]==401
        status,headers,body=request('/api/v1/system/status',{'X-Api-Key':ui,'Cookie':cookie})
        assert status==200,(status,body[:1000])
        print(f'PASS ({method}): real app startup, anonymous setup/API rejection despite local bypass setting, authenticated bootstrap, non-master UI credential, cookie-bound API authentication')
    finally:
        process.send_signal(signal.SIGTERM)
        try: process.wait(timeout=15)
        except subprocess.TimeoutExpired: process.kill();process.wait()
        log.close()
