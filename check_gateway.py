#!/usr/bin/env python3
import os
import time
from scapy.all import conf, get_if_list

# Define options and arguments using argparse
import argparse

def parse_arguments():
  """
  Parses command-line arguments for the script.
  """
  parser = argparse.ArgumentParser(description="Scans for a valid gateway and writes it to a file.")
  parser.add_argument("script_directory", type=str, help="Path to the script directory containing configuration files.")
  return parser.parse_args()

# Function to get script directory (optional, for reference)
def get_script_directory():
  """
  Returns the absolute path of the script directory. (Optional, use when not passing argument)
  """
  return os.path.dirname(os.path.realpath(__file__))

# Domain files relative to the script directory (replace with actual filenames)
def get_domain_files(script_directory):
  """
  Returns a list of domain file paths relative to the script directory.
  """
  return [
    os.path.join(script_directory, "appdomain.txt"),
    os.path.join(script_directory, "badsites.txt"),
    os.path.join(script_directory, "top-10k.txt")
  ]

# Default gateway
default_gateway = "10.1.0.1"


def scan_for_valid_gateway():
  """
  Scans for a valid gateway on interfaces other than 10.1.0.1
  Returns the gateway address if found, otherwise None.
  """
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

def write_gateway_to_file(gateway, script_directory):
  """
  Writes the gateway address to a file in the script directory.
  """
  gateway_file = os.path.join(script_directory, "valid_gateway.txt")
  with open(gateway_file, "w") as f:
    f.write(gateway)
    print(f"Gateway written to '{gateway_file}': {gateway}")

def main():
  # Parse command-line arguments
  args = parse_arguments()
  script_directory = args.script_directory

  # Domain files based on script directory
  domain_files = get_domain_files(script_directory)

  while True:
    gateway = scan_for_valid_gateway()
    if gateway:
      write_gateway_to_file(gateway, script_directory)
      break  # Exit the loop after finding a valid gateway
    else:
      print("No valid gateway found yet. Retrying...")
    time.sleep(10)  # Wait for 10 seconds before retrying

if __name__ == "__main__":
  main()
