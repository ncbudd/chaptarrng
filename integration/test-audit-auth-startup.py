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
from urllib.parse import urlencode

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dotnet', default='dotnet')
parser.add_argument('--app', type=Path, required=True)
parser.add_argument('--log', type=Path, required=True)
parser.add_argument('--misconfigured-oidc', action='store_true')
parser.add_argument('--url-base', default='')
parser.add_argument('--initial-auth-method', choices=('None', 'Forms', 'Basic'), default='None')
args = parser.parse_args()
with tempfile.TemporaryDirectory(prefix='chaptarr-audit-startup-') as temporary:
    data = Path(temporary)
    data.chmod(0o700)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    master = secrets.token_hex(16)
    seerr = secrets.token_hex(16)
    method = 'Oidc' if args.misconfigured_oidc else args.initial_auth_method
    (data/'config.xml').write_text(f'<Config><ApiKey>{master}</ApiKey><SeerrApiKey>{seerr}</SeerrApiKey><BindAddress>127.0.0.1</BindAddress><Port>{port}</Port><UrlBase>{args.url_base}</UrlBase><AuthenticationMethod>{method}</AuthenticationMethod><AuthenticationRequired>DisabledForLocalAddresses</AuthenticationRequired><LaunchBrowser>False</LaunchBrowser><AnalyticsEnabled>False</AnalyticsEnabled><UpdateAutomatically>False</UpdateAutomatically></Config>')
    env = dict(os.environ, DOTNET_GCHeapHardLimit='0x30000000', ASPNETCORE_ENVIRONMENT='Production')
    log = open(args.log, 'w')
    process = subprocess.Popen([args.dotnet, str(args.app.resolve()), '-data='+str(data), '-nobrowser', '-nosingleinstancecheck'], stdout=log, stderr=subprocess.STDOUT, env=env)
    def request(path, headers=None, method='GET', body=None, form=None):
        connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
        headers=dict(headers or {})
        if body is not None:
            body=json.dumps(body)
            headers['Content-Type']='application/json'
        if form is not None:
            body=urlencode(form)
            headers['Content-Type']='application/x-www-form-urlencoded'
        connection.request(method,args.url_base+path,body=body,headers=headers)
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
            assert not headers.get('WWW-Authenticate')
            status,headers,body=request('/')
            assert status==302 and headers.get('Location')==args.url_base+'/login',(status,headers)
            assert not headers.get('WWW-Authenticate')
            token=(data/'setup-token').read_text()
            assert (data/'setup-token').stat().st_mode & 0o777 == 0o600
            authorization='Basic '+base64.b64encode(('setup:'+token).encode()).decode()
            assert request('/initialize.json', {'Authorization': authorization})[0]==200
            status,headers,body=request('/setup', method='POST', form={'setupToken': 'wrong'})
            assert status==302 and headers.get('Location')==args.url_base+'/login?setupFailed=true',(status,headers)
            assert 'Set-Cookie' not in headers
            status,headers,body=request('/setup', method='POST', form={'setupToken': token+'\n'})
            assert status==302 and headers.get('Location')==args.url_base+'/',(status,headers)
            setup_cookie=headers['Set-Cookie'].split(';',1)[0]
            assert setup_cookie.startswith('ChaptarrInitialSetup=')
            assert 'httponly' in headers['Set-Cookie'].lower() and 'samesite=strict' in headers['Set-Cookie'].lower()
            recovery_headers = {'Cookie': setup_cookie}
            assert request('/', recovery_headers)[0] in (200,404)  # The audit build may omit UI assets.
        status,headers,body=request('/initialize.json',recovery_headers)
        assert status==200,(status,body[:200])
        bootstrap=json.loads(body)
        assert bootstrap['setupRequired'] is not args.misconfigured_oidc
        ui=bootstrap['apiKey']
        assert ui.startswith('ui_') and ui!=master
        cookie=headers['Set-Cookie'].split(';',1)[0]
        assert 'httponly' in headers['Set-Cookie'].lower() and 'samesite=strict' in headers['Set-Cookie'].lower()
        assert request('/api/v1/system/status',{'X-Api-Key':ui})[0]==401
        status,headers,body=request('/api/v1/system/status',{'X-Api-Key':ui,'Cookie':cookie})
        assert status==200,(status,body[:1000])
        assert request('/api/v1/calendar/token')[0]==401
        assert request('/api/v1/calendar/token',{'X-Api-Key':seerr})[0] in (401,403)
        status,headers,body=request('/api/v1/calendar/token',{'X-Api-Key':ui,'Cookie':cookie})
        assert status==200,(status,body[:1000])
        calendar=json.loads(body)['token']
        assert calendar.startswith('cal_') and calendar not in (ui,master)
        assert 'no-store' in headers.get('Cache-Control','')
        for name in ('Chaptarr.ics','Readarr.ics'):
            status,headers,body=request('/feed/v1/calendar/'+name+'?calendarToken='+calendar)
            assert status==200 and b'BEGIN:VCALENDAR' in body,(status,body[:1000])
        assert request('/api/v1/system/status?calendarToken='+calendar)[0]==401
        assert request('/api/v1/calendar/token?calendarToken='+calendar)[0]==401
        assert request('/signalr/messages/negotiate?negotiateVersion=1',{'Authorization':'Bearer '+ui},'POST')[0]==401
        assert request('/signalr/messages/negotiate?negotiateVersion=1',{'Authorization':'Bearer '+ui,'Cookie':cookie},'POST')[0]==200
        if not args.misconfigured_oidc:
            status,headers,body=request('/api/v1/config/host',{'X-Api-Key':ui,'Cookie':cookie})
            assert status==200
            settings=json.loads(body)
            password=secrets.token_hex(18)
            settings.update(authenticationMethod='forms',authenticationRequired='enabled',username='audit-owner',password=password,passwordConfirmation=password)
            status,headers,body=request('/api/v1/config/host',{'X-Api-Key':ui,'Cookie':cookie},'PUT',settings)
            assert status in (200,202),(status,body[:1000])
            forms_cookie=headers['Set-Cookie'].split(';',1)[0]
            assert request('/initialize.json', {'Cookie': setup_cookie, 'Accept': 'application/json'})[0]==401
            assert request('/setup', method='POST', form={'setupToken': token})[0]==404
            assert request('/api/v1/system/status',{'X-Api-Key':ui,'Cookie':cookie+'; '+forms_cookie})[0]==401
            status,headers,body=request('/initialize.json',{'Cookie':forms_cookie,'Accept':'application/json'})
            assert status==200,(status,body[:1000])
            bootstrap=json.loads(body)
            assert not bootstrap['setupRequired']
            renewed=bootstrap['apiKey']
            renewed_cookie=headers['Set-Cookie'].split(';',1)[0]
            assert renewed!=ui and renewed.startswith('ui_')
            assert request('/api/v1/system/status',{'X-Api-Key':renewed,'Cookie':forms_cookie+'; '+renewed_cookie})[0]==200
            print('PASS: first-run account creation revokes the old UI token and the preserved Forms cookie obtains a usable replacement')
        print(f'PASS ({method}): real startup, anonymous setup/API rejection despite local bypass, private setup password, cookie-bound UI API/SignalR access, read-only external calendar subscription without master-key exposure')
    finally:
        process.send_signal(signal.SIGTERM)
        try: process.wait(timeout=15)
        except subprocess.TimeoutExpired: process.kill();process.wait()
        log.close()
