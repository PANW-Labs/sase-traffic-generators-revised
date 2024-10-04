#!/usr/bin/env python3
import os
import subprocess

# Define paths and configurations
script_directory = "/home/lab-user/scripts/sase-traffic-generators/"
gateway_file_path = os.path.join(script_directory, "valid_gateway.txt")  # Path to the valid gateway file
run_traffic_script = os.path.join(script_directory, "run_gp_traffic_gen.py")  # Path to the traffic generator script

# List of domain files you want to create services for
domain_files = [
    "appdomain.txt",
    "badsites.txt",
    "top-10k.txt"
]

def create_traffic_generator_script():
    """Creates the run_gp_traffic_gen.py script."""
    script_content = f"""#!/usr/bin/env python3
import os
import sys

script_directory = "{script_directory}"
gateway_file_path = os.path.join(script_directory, "valid_gateway.txt")

def get_gateway():
    \"\"\"Read the gateway from the valid_gateway.txt file.\"\"\"
    with open(gateway_file_path, 'r') as f:
        gateway = f.read().strip()
    return gateway

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: run_gp_traffic_gen.py <domain_file>")
        sys.exit(1)

    domain_file = sys.argv[1]
    gateway = get_gateway()

    if not gateway:
        print("No valid gateway found in valid_gateway.txt")
        sys.exit(1)

    # Execute the traffic generator command
    command = f"/usr/bin/python3 gp-traffic-gen.py --domains {{domain_file}} --insecure --gateway {{gateway}}"
    os.system(command)
"""
    with open(run_traffic_script, "w") as f:
        f.write(script_content)
    os.chmod(run_traffic_script, 0o755)  # Make the script executable

def create_service_file(filename):
    """Generates a systemd service file for the given domain file."""
    service_content = f"""
[Unit]
Description=GP Traffic Generator - {filename}
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
WorkingDirectory={script_directory}
ExecStartPre=/bin/bash -c 'while [ ! -s {gateway_file_path} ]; do sleep 5; done'
ExecStart=/usr/bin/python3 {run_traffic_script} {filename}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    service_filename = f"{filename}.service"
    service_file_path = os.path.join("/etc/systemd/system", service_filename)

    with open(service_file_path, "w") as f:
        f.write(service_content)

    print(f"Service file created: {service_file_path}")

def create_service_files():
    """Creates service files for each domain file."""
    for domain_file in domain_files:
        create_service_file(domain_file)

def main():
    """Main function to set up the entire traffic generator service."""
    os.makedirs(script_directory, exist_ok=True)  # Ensure the script directory exists
    create_traffic_generator_script()  # Create the traffic generator script
    create_service_files()  # Create the service files

    # Reload systemd, enable and start the services
    subprocess.run(["sudo", "systemctl", "daemon-reload"])

    for domain_file in domain_files:
        subprocess.run(["sudo", "systemctl", "enable", f"{domain_file}.service"])
        subprocess.run(["sudo", "systemctl", "start", f"{domain_file}.service"])

    print("All services have been enabled and started.")

if __name__ == "__main__":
    main()
