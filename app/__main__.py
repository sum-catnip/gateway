from app.docker.srvgen.service import load_services
from app import paths
from app.config import config
from app.fs_handler import Handler

import os
import sys
import time
import signal
import logging
import threading
from pathlib import Path
from typing import Container, Optional, Any
from itertools import chain
from operator import attrgetter
from threading import Thread

import docker
from watchdog.observers import Observer

import sdnotify

def sigterm_handler(_signo, _stack_frame):
    # Raises SystemExit(0):
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)

logging.basicConfig(level=logging.getLevelName(config.log_level))
logger = logging.getLogger(__name__)
docker_logger = logging.getLogger("container")

client = docker.DockerClient(**config.docker)
logger.info('building docker image, this coult take a while')
_, logs = client.images.build(path=str(Path(__file__).parent / 'docker'), rm=True, pull=True, tag='gateway')
for chunk in logs:
    if 'stream' in chunk:
        for line in chunk['stream'].splitlines(): docker_logger.debug(line)

logger.info('built gateway docker image!')

reload_evt = threading.Event()

def reload(container) -> Container:
    logger.info('services modified, reloading..')
    try: 
        hosts = load_services(paths.srv_dir)
        service_flat = chain.from_iterable(map(attrgetter('service'), hosts))
        expose_flat = chain.from_iterable(map(attrgetter('expose'), service_flat))
        if container: container.stop()
        container = client.containers.run(
            'gateway',
            detach=True,
            auto_remove=True,
            environment={
                'PUID': os.getuid(),
                'PGID': os.getgid(),
                'SERVERURL': config.wireguard.address,
                'SERVERPORT': config.wireguard.port,
                'PEERDNS': config.wireguard.dns,
                'INTERNAL_SUBNET': config.wireguard.subnet,
                'ALLOWEDIPS': config.wireguard.allowed_ips,
                'LOG_LEVEL': config.log_level
            },
            ports={
                f'{config.wireguard.port}/udp' : config.wireguard.port,
                **{f'{e.public}/{e.protocol}'  : e.public for e in expose_flat}
            },
            sysctls={'net.ipv6.conf.all.disable_ipv6': 0},
            cap_add=['NET_ADMIN', 'SYS_MODULE'],
            volumes={
                config.wireguard.modules: {
                    'bind': '/lib/modules',
                    'mode': 'ro'
                },
                str(paths.srv_dir):{
                    'bind': '/services',
                    'mode': 'ro'
                },
                str(paths.out_dir):{
                    'bind': '/config',
                    'mode': 'rw'
                }
            })
        
        def log():
            for l in container.logs(stream=True, follow=True):
                l = l.decode('utf-8').strip()
                if 'error' in l.lower(): docker_logger.error(l)
                if l.startswith('****'): docker_logger.info(l)
                else: docker_logger.debug(l)
            logger.debug('container stopped')
        Thread(target=log).start()
    except Exception as e: docker_logger.error(str(e))
    return container


# Inform systemd that we've finished our startup sequence...
# n = sdnotify.SystemdNotifier()
# n.notify("READY=1")

handler = Handler(reload_evt, ['*.toml'])
observer = Observer()
observer.schedule(handler, str(paths.srv_dir), recursive=True)
observer.start()

container = reload(None)
try:
    while True:
        reload_evt.wait()
        container = reload(container)
        reload_evt.clear()
finally:
    logger.info('exiting')
    if container: container.stop()
    observer.stop()
    observer.join()