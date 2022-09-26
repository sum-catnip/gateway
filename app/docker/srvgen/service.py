from dataclasses import dataclass
from typing import List, Dict, Any, Type, Tuple
from pathlib import Path
from functools import partial

import toml

class MalformedService(Exception):
    def __init__(self, msg: str, cfg: str):
        super().__init__(f'{msg} in service config' + (f':\n{cfg}' if cfg else ''))

class DuplicatePort(Exception):
    def __init__(self, port: int, srv1: str, srv2: str):
        super().__init__(f'error in srv {srv2}; port {port} already exposed in srv {srv1}')

class DuplicateService(Exception):
    def __init__(self, srv: str):
        super().__init__(f'service "{srv}" is defined multiple times')

#PUBLIC_PORTS: Dict[str, str] = {}

@dataclass
class Expose:
    public: int
    internal: int
    protocol: str = 'tcp'

    @classmethod
    def parse(cls: Type['Expose'], d: Dict[str, Any], srv: str) -> 'Expose':
        try:
            proto = d.get('protocol') or 'tcp'
            p = int(d['public'])
            if not (1 <= p <= 65535): raise ValueError

            #dupe = PUBLIC_PORTS.get(f'{p}/{proto}')
            #if dupe: raise DuplicatePort(p, dupe, srv)
            #else: PUBLIC_PORTS[f'{p}/{proto}'] = srv

            i = int(d.get('internal') or p)
            if not (1 <= i <= 65535): raise ValueError
        except KeyError:
            raise MalformedService('"public" field missing', toml.dumps(d))
        except ValueError as e:
            raise MalformedService(f'invalid port value "{str(e)}"', toml.dumps(d))
        
        return cls(p, i, proto)

@dataclass
class Service:
    name: str
    expose: List[Expose]

    @classmethod
    def parse(cls: Type['Service'], d: Dict[str, Any]) -> 'Service':
        try: name = d['name']
        except KeyError: raise MalformedService(f'"name" field missing', toml.dumps(d))
        return cls(name, list(map(partial(Expose.parse, srv=name), d.get('expose') or [])))

@dataclass
class Host:
    name: str
    service: Tuple[Service]

def load_services(p: Path) -> Tuple[Host]:
    #PUBLIC_PORTS.clear()
    hosts = tuple(
        map(
            lambda hp: 
                Host(hp.name, tuple(map(Service.parse, map(toml.load, hp.rglob('*.toml'))))),
            p.glob('*')
        )
    )
    # check duplicate names
    #try: raise DuplicateService(
    #    next(filter(lambda s1: sum(1 for _ in (s2.name == s1.name for s2 in services)) > 1, services)).name)
    #except StopIteration: pass
    return hosts