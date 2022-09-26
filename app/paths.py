from app import const

import os
import appdirs
from pathlib import Path

os.environ['XDG_CONFIG_DIRS'] = '/etc:/usr/local/etc'
euid = os.geteuid()

def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p

if euid == 0: config_dir = ensure_dir(Path(appdirs.site_config_dir(const.app, const.author)))
else:         config_dir = ensure_dir(Path(appdirs.user_config_dir(const.app, const.author)))

config = config_dir / 'config.toml'

srv_dir = ensure_dir(config_dir / 'services')
out_dir = ensure_dir(config_dir / 'out')