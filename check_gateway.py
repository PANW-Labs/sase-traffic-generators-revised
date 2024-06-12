#!/usr/bin/env python3
import os
import time
from scapy.all import conf, get_if_list

# Define Git repository URL
script_repo_url = "http://github.com/khindaraj/sase-traffic-generators.git"

# Set working directory (replace with your actual directory)
working_directory = "/home/lab-user/scripts"

# Define Git directory within the working directory (replace with the actual subdirectory)
script_directory = os.path.join(working_directory, "sase-traffic-generators")  # Subdirectory within working_directory

# Domain files relative to the script directory (replace with actual filenames)
domain_files = [
    os.path.join(script_directory, "appdomain.txt"),
    os.path.join(script_directory, "badsites.txt"),
    os.path.join(script_directory, "top-10k.txt")
]

# Default gateway
default_gateway = "10.1.0.1"


def scan_for_valid_gateway():
    #Scans for a valid gateway on interfaces other than 10.1.0.1
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
    script_directory = os.path.dirname(os.path.realpath(__file__))
    while True:
        gateway = scan_for_valid_gateway()
        if gateway:
            print(f"Found valid gateway: {gateway}")
            # Write the gateway to a file for the gateway checker service to read
            with open(os.path.join(script_directory, "valid_gateway.txt"), "w") as f:
                f.write(gateway)
        else:
            print("No valid gateway found yet. Retrying...")
        time.sleep(10)  # Wait for 10 seconds before retrying

if __name__ == "__main__":
    main()