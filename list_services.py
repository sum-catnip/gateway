from app.docker.srvgen.service import load_services
from app import paths

import sys

try: host = sys.argv[1]
except IndexError: host = None

hosts = load_services(paths.srv_dir)
try:
    if host: hosts = [next(filter(lambda h: h.name == host, hosts))]
except StopIteration: raise SystemExit(f'host {host} is not registered')

for h in hosts:
    print(f'host {h.name}:')
    for s in h.service:
        print(f'--- srv {s.name}')
        for e in s.expose:
            print(f'--- --- {e.public: <5} -> {e.internal: <5} / {e.protocol}')