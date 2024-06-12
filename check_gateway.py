#!/usr/bin/env python3
import subprocess
from scapy.all import conf, get_if_list

def scan_for_valid_gateway():
    """Scans for a valid gateway on interfaces other than 10.1.0.1."""
    interfaces = get_if_list()
    for interface in interfaces:
        try:
            route = conf.route.route("0.0.0.0", iface=interface)
            gateway = route[2]
            if gateway and gateway != "10.1.0.1":
                return gateway
        except Exception as e:
            print(f"Error scanning interface {interface}: {e}")
    return None

def main():
    gateway = scan_for_valid_gateway()
    if gateway:
        print(gateway)
    else:
        print("No valid gateway found")

if __name__ == "__main__":
    main()
