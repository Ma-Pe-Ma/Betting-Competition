import requests
import requests_unixsocket

requests_unixsocket.monkeypatch()

r = requests.get('http+unix://%2FBettingInstance%2Fgunicorn.socket/sign-in')
assert r.status_code == 200