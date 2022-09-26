from service import load_services, Expose

import os
import sys
import logging
import configparser
from typing import List
from pathlib import Path
from subprocess import run
from operator import attrgetter
from functools import partial
from itertools import chain

logging.basicConfig(level=logging.getLevelName(os.environ.get('LOG_LEVEL') or 'INFO'))
logger = logging.getLogger(__name__)

def critical(msg: str):
    logger.critical(f'*ERROR* {msg}')
    run(['sleep', 'infinity'])
    # just to make the linters happy
    exit(1)

try: HOSTS = load_services(Path('/services'))
except Exception as e: critical(str(e))


def conf(path: str) -> configparser.ConfigParser:
    # ignores duplicate sections but i dont care as i just need the first one
    config = configparser.ConfigParser(strict=False)
    config.read(path)
    return config

def run_iptables(args: List[str]):
    cmd = ['iptables', *args]
    logger.debug(' '.join(cmd))
    try: run(cmd).check_returncode()
    except Exception as e: critical(str(e))


def expose_iptables(action: str, eth: str, wg: str, e: Expose, ip: str):
    # prerouting
    # forwards traffic from the outside world to the appropriate vpn client
    # by changing the destination address
    run_iptables([
        # use nat table so we get access to the routing chains
        '-t', 'nat',
        action,
        # when packet hits the interface
        'PREROUTING',
        # the interface
        '-i', eth,
        # match protocol
        '-p', e.protocol,
        # load protocol extensions to use --dport
        '-m', e.protocol,
        # enable rule for target port
        '--dport', str(e.public),
        # nat type to use
        # DNAT changes the destination address to the service ip and port
        '-j', 'DNAT', '--to-destination', f'{ip}:{e.internal}'])

    # forwarding
    # allow forwarding packets from outside into the vpn network
    # to establish new connections
    run_iptables([
        action,
        'FORWARD',
        # from outside interface
        '-i', eth,
        # into the vpn interface
        '-o', wg,
        # match protocol
        '-p', e.protocol,
        # load protocol extensions to use --dport
        '-m', e.protocol,
        # enable rule for target port
        '--dport', str(e.public),
        # only applies to the following tcp-flags
        *(['--tcp-flags', 'FIN,SYN,RST,ACK', 'SYN'] if e.protocol == 'tcp' else []),
        # use conntrack module
        '-m', 'conntrack',
        # for new connections only
        '--ctstate', 'NEW',
        # allow
        '-j', 'ACCEPT'])

def iptables(wg: str, eth: str, action: str):
    logger.info('generating iptables rules')

    # for now i only support /24 networks
    subnet = f'{os.environ.get("INTERNAL_SUBNET") or "10.13.13.0"}/24'

    # get ip for service
    host2ip = lambda s: conf(f'/config/peer_{s}/peer_{s}.conf')['Interface']['Address']

    # don't allow vpn clients communicating with each other (from wg0 to wg0)
    run_iptables([action, 'FORWARD', '-i', wg, '-o', wg, '-m', 'conntrack', '--ctstate', 'NEW', '-j', 'DROP'])
    
    # allow forwarding from the vpn to the outside
    run_iptables([action, 'FORWARD', '-i', wg, '-o', eth, '-j', 'ACCEPT'])

    # allow all forwarding (outside to vpn) on already established connections
    run_iptables([action, 'FORWARD', '-i', eth, '-o', wg, '-m', 'conntrack', '--ctstate', 'RELATED,ESTABLISHED', '-j', 'ACCEPT'])
 
    # hides vpn network traffic behind server ip (NAT) by replacing the from and to address
    # and tracking connections
    run_iptables(['-t', 'nat', action, 'POSTROUTING', '-s', subnet, '-o', eth, '-j', 'MASQUERADE'])

    for host in HOSTS:
        for e in chain.from_iterable(map(attrgetter('expose'), host.service)):
            expose_iptables(action, eth, wg, e, host2ip(host.name))

def gen_conf():
    if not HOSTS:
        critical('!!! NO SERVICES CONFIGURED IN /services. NOTHING TO DO... !!!')

    logger.info('generating configs')
    os.environ['PEERS'] = ','.join(map(attrgetter('name'), HOSTS))
    run(['/bin/bash', '/app/srvgen/confs'])

{
    'cfg':  gen_conf,
    'up':   partial(iptables, action='-A'),
    'down': partial(iptables, action='-D')
}[sys.argv[1]](*sys.argv[2:])