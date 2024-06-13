#!/bin/bash

# Update the script header to accept one argument
script_path="$1"

while true; do
  if [[ -f "$script_path" ]]; then
    # Use the passed script_path
    gateway=$(cat "$script_path")
    if [[ ! -z "${gateway}" ]]; then
      echo "Found valid gateway: ${gateway}"
      python3 "$(dirname "$script_path")"/create_traffic_services.py "${gateway}"
      break
    fi
  else
    echo "Waiting for valid gateway..."
    sleep 10
  fi
done
