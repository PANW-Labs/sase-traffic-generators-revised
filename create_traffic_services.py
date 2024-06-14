#!/usr/bin/env python3
import os
import subprocess
import sys

script_directory = "/home/lab-user/scripts/sase-traffic-generators/"  # Update with your script directory
domain_files = [
    os.path.join(script_directory, "appdomain.txt"),
    os.path.join(script_directory, "badsites.txt"),
    os.path.join(script_directory, "top-10k.txt")
]

def create_traffic_generator_service(filename, filename_full, gateway):
    gateway_argument = f"--gateway {gateway}"

    service_content = f"""
[Unit]
Description=GP Traffic Generator - {filename}
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
#User=lab-user  # Replace with your username
WorkingDirectory={script_directory}
ExecStart=/usr/bin/python3 gp-traffic-gen.py --domains {filename_full} --insecure {gateway_argument}

[Install]
WantedBy=multi-user.target
"""

    service_filename = f"{filename}.service"
    with open(os.path.join("/etc/systemd/system", service_filename), "w") as f:
        f.write(service_content)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: script.py <gateway>")
        sys.exit(1)

    gateway = sys.argv[1]
    for domain_file in domain_files:
        filename = os.path.splitext(os.path.basename(domain_file))[0]
        filename_full = f"{filename}.txt"  # Add the .txt extension here
        create_traffic_generator_service(filename, filename_full, gateway)

    subprocess.run(["sudo", "systemctl", "daemon-reload"])
    for domain_file in domain_files:
        filename = os.path.splitext(os.path.basename(domain_file))[0]
        subprocess.run(["sudo", "systemctl", "enable", f"{filename}.service"])
        subprocess.run(["sudo", "systemctl", "start", f"{filename}.service"])

