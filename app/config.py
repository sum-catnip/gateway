from app import paths

from dataclasses import dataclass, field, asdict
from typing import Dict, Any

import toml

@dataclass
class Wireguard:
    port: int = 51820
    address: str = 'auto'
    dns: str = '8.8.8.8'
    subnet: str = '10.13.13.0'
    allowed_ips: str = '0.0.0.0/0'
    modules: str = '/lib/modules'

@dataclass
class Config:
    log_level: str = 'INFO'
    wireguard: Wireguard = field(default_factory=Wireguard)
    docker: Dict[str, Any] = field(default_factory=dict)

if paths.config.exists():
    d = toml.load(paths.config)
    config = Config(d['log_level'], Wireguard(**d['wireguard'], **d['docker']))
else:
    config = Config()
    toml.dump(asdict(config), paths.config.open('wt'))