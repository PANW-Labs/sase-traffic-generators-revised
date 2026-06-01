#! /usr/bin/env python3

"""
Palo Alto Networks
Generate traffic for lab environments
mkorenbaum@paloaltonetworks.com
"""

import requests
import time
import random
import argparse
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import urllib3
import platform
import subprocess
from requests.adapters import HTTPAdapter


urllib3.disable_warnings()
# Global Vars

timer = 10800
SCRIPT_NAME = "SASE Demo Traffic Generator"
TIME_BETWEEN_REQUESTS = 5
MY_LOG_FILE = "sase-traffic-log.txt"
BACKOFF_PRUNE_INTERVAL = 300  # prune expired backoff entries every 5 minutes


if not os.path.exists(MY_LOG_FILE):
    with open(MY_LOG_FILE, 'w') as fp:
        fp.write("Creating SASE Traffic Generator Log File \n")
        pass

def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    return subprocess.call(command) == 0

def readFile(fileName):
    with open(fileName, "r") as f:
        return [line for line in f.read().splitlines() if line.strip()]

def getRandomUrl(mylist):
    return random.choice(mylist)

def isBackedoff(key, db):
    expiry = db.get(key)
    if expiry is None:
        return False
    if time.time() >= expiry:
        del db[key]   # lazy eviction — removes entry as soon as it expires
        return False
    return True

def pruneBackoff(db):
    """Remove all expired entries to prevent unbounded dict growth."""
    now = time.time()
    expired = [k for k, v in db.items() if v <= now]
    for k in expired:
        del db[k]

def makeSession():
    """Session with bounded connection pools to prevent socket exhaustion."""
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=4,
        pool_maxsize=8,
        max_retries=0,
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def go():
    ############################################################################
    # Begin Script, parse arguments.
    ############################################################################
    BACKOFF_DB = {}

    # Parse arguments
    parser = argparse.ArgumentParser(description="{0}.".format(SCRIPT_NAME))


    # Specify domain list file and other optional arguments
    options = parser.add_argument_group('Options')
    options.add_argument("--domains", "-d",
                                  help="List of hosts with /r as delimeter, ex. C:/Users/Admin/Desktop/appdomain.txt", required=True,
                                  default=None)
    options.add_argument("--gateway", "-g",
                         help="Provide the default gateway to prevent the traffic generation from starting until reachable - default 10.0.0.1",
                         required=False,
                         default=None)

    options.add_argument("--insecure", "-I", help="Disable SSL certificate and hostname verification",
                                  dest='verify', action='store_false', default=True)

    debug_group = parser.add_argument_group('Debug', 'These options enable debugging output')
    debug_group.add_argument("--debug", "-D", help="Print Debug info to stdout", action='store_true')

    args = vars(parser.parse_args())


    ############################################################################
    # End Login handling, begin script..
    ############################################################################

    # Set NON-SYSLOG logging to use function name
    logger = logging.getLogger(__name__)

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s',
                                  '%m-%d-%Y %H:%M:%S')

    file_handler = RotatingFileHandler(MY_LOG_FILE, maxBytes=10000000, backupCount=2)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Print to stdout if debug flag enabled
    if args['debug']:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

    # check if default gateway IP has been overridden
    GATEWAY = '10.0.0.1'
    if args['gateway']:
        GATEWAY = args['gateway']

    # Prior to starting main loop check if Gateway is reachable
    result = ping(GATEWAY)
    while result != True:
        print("Gateway unreachable will retry again in 3 seconds")
        time.sleep(3)
        result = ping(GATEWAY)

    print("Gateway is NOW REACHABLE Starting Traffic Generation")

    # Load domain list once; reload only when the file changes on disk
    domain_mtime = os.path.getmtime(args['domains'])
    mylist = readFile(args['domains'])
    logger.info("Running {0} Against Provided List: {1} ({2} domains)".format(
        SCRIPT_NAME, args['domains'], len(mylist)))

    session = makeSession()
    last_prune = time.time()

    try:
        while True:
            # Hot-reload domain list only when file changes — avoids re-reading
            # on every iteration which causes page-cache churn and heap pressure
            current_mtime = os.path.getmtime(args['domains'])
            if current_mtime != domain_mtime:
                mylist = readFile(args['domains'])
                domain_mtime = current_mtime
                logger.info("Domain list reloaded: %d entries", len(mylist))

            # Periodically evict expired backoff entries to prevent dict growth
            now = time.time()
            if now - last_prune >= BACKOFF_PRUNE_INTERVAL:
                pruneBackoff(BACKOFF_DB)
                last_prune = now

            myurl = getRandomUrl(mylist)

            for scheme in ('http', 'https'):
                mykey = scheme + '_' + myurl
                if isBackedoff(mykey, BACKOFF_DB):
                    logger.error("Currently backed off for:  " + mykey)
                    continue
                url = scheme + '://' + myurl
                try:
                    logger.info("trying to connect to " + url)
                    # stream=True prevents the response body from being loaded
                    # into memory; the context manager closes the socket cleanly
                    with session.get(url, timeout=15, verify=args['verify'],
                                     stream=True) as resp:
                        status = resp.status_code
                    logger.info("Request to " + myurl + " status= " + str(status))
                except requests.exceptions.RequestException as e:
                    logger.error(e)
                    BACKOFF_DB[mykey] = time.time() + timer
                    logger.error("Backoff Val: " + str(BACKOFF_DB[mykey]))

            time.sleep(random.randrange(0, TIME_BETWEEN_REQUESTS))

    except KeyboardInterrupt:
        logger.info("Shutting down")
    finally:
        session.close()

if __name__ == "__main__":
    go()
