
import os
import time
import subprocess

def get_gateway():
  """
  Retrieves the default gateway address using the 'ip route' command,
  excluding the provided address.
  """
  try:
    output = subprocess.check_output(["ip", "route", "show"]).decode("utf-8")
    for line in output.splitlines():
      if "default via" in line and not "10.1.0.1" in line:
        gateway = line.split()[2]
        return gateway
  except subprocess.CalledProcessError as e:
    print(f"Error getting gateway: {e}")
    return None

def write_gateway_to_file(gateway, output_file):
  """
  Writes the gateway address to a specified file.
  """
  if gateway:
    with open(output_file, "w") as f:
      f.write(gateway)
      print(f"Gateway found (excluding 10.1.0.1): {gateway}")

def main():
  # Get output file path from script argument
  if len(sys.argv) != 2:
    print("Usage: python script.py output_file.txt")
    exit(1)
  output_file = sys.argv[1]

  # Loop infinitely until a valid gateway (excluding 10.1.0.1) is found
  while True:
    gateway = get_gateway()
    if gateway:
      write_gateway_to_file(gateway, output_file)
      print(f"Gateway found (excluding 10.1.0.1): {gateway}")
      break  # Exit loop upon finding a valid gateway
    else:
      print("No gateway assigned yet (excluding 10.1.0.1). Trying again...")
      time.sleep(5)  # Add a delay between retries (adjustable)

if __name__ == "__main__":
  import sys
  main()
